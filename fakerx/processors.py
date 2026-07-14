# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:14
# @Software  : PyCharm
# @FileName  : processors.py
# -----------------------------
"""
数据后处理器 - 生成后对数据进行变换、清洗、格式化
"""

import re
import hashlib
from typing import Any, Dict, List, Optional, Callable


class PostProcessor:
    """
    数据后处理器

    在 Schema 生成原始数据后，对数据进行二次处理:
    - 字段变换 (大小写、格式化、哈希)
    - 数据清洗 (去空、去重)
    - 自定义处理函数
    """

    # 内置处理器
    BUILTIN_PROCESSORS = {
        'upper': lambda v: str(v).upper() if v else v,
        'lower': lambda v: str(v).lower() if v else v,
        'strip': lambda v: str(v).strip() if v else v,
        'title': lambda v: str(v).title() if v else v,
        'md5': lambda v: hashlib.md5(str(v).encode()).hexdigest() if v else v,
        'sha256': lambda v: hashlib.sha256(str(v).encode()).hexdigest() if v else v,
        'base64': lambda v: __import__('base64').b64encode(str(v).encode()).decode() if v else v,
        'none_if_empty': lambda v: None if v in ('', [], {}, None) else v,
        'round2': lambda v: round(float(v), 2) if v is not None else v,
        'round4': lambda v: round(float(v), 4) if v is not None else v,
        'to_int': lambda v: int(v) if v is not None else v,
        'to_str': lambda v: str(v) if v is not None else v,
        'to_float': lambda v: float(v) if v is not None else v,
    }

    def __init__(self):
        self._custom_processors: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """注册自定义处理器"""
        self._custom_processors[name] = func

    def process_field(self, value: Any, processors: List[str]) -> Any:
        """
        对单个字段值应用一系列处理器

        Args:
            value: 原始值
            processors: 处理器名称列表，按顺序执行

        Example:
            >>> pp = PostProcessor()
            >>> pp.process_field('  Hello  ', ['strip', 'upper'])
            'HELLO'
            >>> pp.process_field('secret', ['md5'])
            '5ebe2294edd0e0c08fae...'
        """
        result = value
        for proc_name in processors:
            func = self._custom_processors.get(proc_name) or \
                   self.BUILTIN_PROCESSORS.get(proc_name)
            if func is None:
                raise ValueError(f"未知的处理器: '{proc_name}'")
            result = func(result)
        return result

    def process_record(
        self,
        record: Dict,
        field_processors: Dict[str, List[str]],
    ) -> Dict:
        """
        对整条记录应用处理器

        Args:
            record: 原始记录
            field_processors: {字段名: [处理器名, ...]}

        Example:
            >>> pp.process_record(
            ...     {'name': '  zhang  ', 'price': '12.345'},
            ...     {'name': ['strip', 'title'], 'price': ['round2']}
            ... )
            {'name': 'Zhang', 'price': 12.35}
        """
        result = record.copy()
        for field, processors in field_processors.items():
            if field in result:
                result[field] = self.process_field(result[field], processors)
        return result

    def process_records(
        self,
        records: List[Dict],
        field_processors: Dict[str, List[str]],
    ) -> List[Dict]:
        """批量处理记录"""
        return [
            self.process_record(record, field_processors)
            for record in records
        ]

    def deduplicate(
        self,
        records: List[Dict],
        key_fields: List[str],
        keep: str = 'first',
    ) -> List[Dict]:
        """
        按指定字段去重

        Args:
            records: 记录列表
            key_fields: 去重依据的字段
            keep: 'first' 保留第一条, 'last' 保留最后一条
        """
        seen = set()
        result = []
        for record in records:
            key = tuple(record.get(f) for f in key_fields)
            if key not in seen:
                seen.add(key)
                if keep == 'last':
                    result.append(record)
                else:
                    result.append(record)
            elif keep == 'last':
                # 替换已存在的记录（保留最后一条）
                for i, r in enumerate(result):
                    if tuple(r.get(f) for f in key_fields) == key:
                        result[i] = record
                        break
        return result
