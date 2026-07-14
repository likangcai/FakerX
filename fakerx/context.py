# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:15
# @Software  : PyCharm
# @FileName  : context.py
# -----------------------------
"""
上下文感知引擎 - 序列号生成、全局状态、跨记录引用、数据生成链
"""

import itertools
import re
import threading
from typing import Any, Dict, List, Optional, Callable, Generator


def parse_sequence_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解析序列号 token，如 {seq:name:start:step}

    Args:
        token: 格式如 '{seq:name}', '{seq:name:100}', '{seq:name:1:2}'

    Returns:
        {'name': str, 'start': int, 'step': int} 或 None（不是序列号 token）
    """
    match = re.match(r'^\{seq:(\w+)(?::(\d+))?(?::(\d+))?\}$', token)
    if not match:
        return None
    name = match.group(1)
    start = int(match.group(2)) if match.group(2) else 1
    step = int(match.group(3)) if match.group(3) else 1
    return {'name': name, 'start': start, 'step': step}


class GenerationContext:
    """
    全局生成上下文

    维护跨记录的全局状态，支持:
    - 自增序列号
    - 全局变量
    - 跨记录引用（如：每条记录的 user_id 引用第 N 条用户的 id）
    - 数据生成链（前一条记录的输出作为后一条记录的输入）
    """

    def __init__(self):
        self._sequences: Dict[str, itertools.count] = {}
        self._globals: Dict[str, Any] = {}
        self._records: List[Dict] = []  # 已生成的所有记录
        self._lock = threading.Lock()
        self._hooks: Dict[str, List[Callable]] = {
            'before_record': [],
            'after_record': [],
        }

    # ----------------------------------------------------------------
    # 序列号
    # ----------------------------------------------------------------

    def sequence(self, name: str, start: int = 1, step: int = 1) -> int:
        """
        获取序列号的下一个值

        Example:
            >>> ctx.sequence('user_id')  # 1
            >>> ctx.sequence('user_id')  # 2
            >>> ctx.sequence('user_id')  # 3
        """
        if not name or not name.strip():
            raise ValueError("序列号名称不能为空")
        with self._lock:
            if name not in self._sequences:
                self._sequences[name] = itertools.count(start, step)
            return next(self._sequences[name])

    def reset_sequence(self, name: str, start: int = 1, step: int = 1):
        """重置序列号"""
        with self._lock:
            self._sequences[name] = itertools.count(start, step)

    # ----------------------------------------------------------------
    # 全局变量
    # ----------------------------------------------------------------

    def set_global(self, key: str, value: Any):
        """设置全局变量"""
        self._globals[key] = value

    def get_global(self, key: str, default: Any = None) -> Any:
        """获取全局变量"""
        return self._globals.get(key, default)

    # ----------------------------------------------------------------
    # 跨记录引用
    # ----------------------------------------------------------------

    def add_record(self, record: Dict):
        """记录已生成的数据，供后续引用"""
        self._records.append(record)

    def get_records(self) -> List[Dict]:
        """获取所有已生成的记录"""
        return self._records.copy()

    def get_record(self, index: int) -> Optional[Dict]:
        """按索引获取已生成的记录"""
        if 0 <= index < len(self._records):
            return self._records[index]
        return None

    def pick_from_records(self, field: str, strategy: str = 'random') -> Any:
        """
        从已生成的记录中提取字段值

        Args:
            field: 字段路径，支持点号嵌套 'profile.level'
            strategy: 选取策略
                'random' - 随机选取
                'first' - 选第一条
                'last' - 选最后一条
                'round_robin' - 轮询选取
        """
        if not self._records:
            raise ValueError("没有已生成的记录，无法引用")

        if strategy == 'first':
            record = self._records[0]
        elif strategy == 'last':
            record = self._records[-1]
        elif strategy == 'round_robin':
            idx = len(self._records) % len(self._records)
            record = self._records[idx - 1] if idx > 0 else self._records[0]
        else:  # random
            import random
            record = random.choice(self._records)

        return self._get_nested_value(record, field)

    @staticmethod
    def _get_nested_value(data: Dict, path: str) -> Any:
        """按点号路径获取嵌套值"""
        current = data
        for part in path.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    # ----------------------------------------------------------------
    # 生命周期钩子
    # ----------------------------------------------------------------

    def register_hook(self, event: str, func: Callable):
        """注册生命周期钩子"""
        if event in self._hooks:
            self._hooks[event].append(func)
        else:
            self._hooks[event] = [func]

    def add_hook(self, event: str, func: Callable):
        """register_hook 的别名，用于兼容"""
        self.register_hook(event, func)

    def run_hooks(self, event: str, *args):
        """运行指定事件的所有钩子，将 self（上下文）作为第一个参数传递"""
        for hook in self._hooks.get(event, []):
            hook(self, *args)

    # ----------------------------------------------------------------
    # 重置
    # ----------------------------------------------------------------

    def reset(self):
        """重置所有上下文状态"""
        with self._lock:
            self._sequences.clear()
            self._globals.clear()
            self._records.clear()
            self._hooks = {
                'before_record': [],
                'after_record': [],
            }
