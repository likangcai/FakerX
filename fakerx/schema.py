# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 14:48
# @Software  : PyCharm
# @FileName  : schema.py
# -----------------------------
"""
Schema 生成引擎 - 支持字段引用、条件逻辑、跨表关联
"""

import re
import random
from typing import Any, Dict, List, Optional, Generator
from .exceptions import SchemaError


class SchemaGenerator:
    """增强版 Schema 生成器"""

    # 引用语法: ${field_name} 或 ${parent.field_name}
    REF_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, faker_instance, context=None):
        self.faker = faker_instance
        self._context = {}  # 当前记录的上下文（用于字段引用）
        self._ext_data = {}  # 外部数据（用于跨表关联）
        self._generation_context = context  # 全局生成上下文（序列号、全局变量等）

    def generate(
            self,
            schema: Dict,
            iterations: int = 1,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        生成结构化数据

        Args:
            schema: Schema 定义字典
            iterations: 生成条数
            unique_fields: 需要保证唯一的字段列表
            foreign_keys: 跨表关联定义
                {'user_id': (external_data, 'id')}
                表示 user_id 字段从 external_data 的 id 列中取值
        Returns:
            生成的数据列表
        """
        unique_tracker = {f: set() for f in (unique_fields or [])}
        self._ext_data = foreign_keys or {}
        results = []

        for i in range(iterations):
            self._context = {}  # 每条记录重置上下文
            record = self._generate_record(schema, unique_tracker)
            results.append(record)

        return results

    def generate_stream(
            self,
            schema: Dict,
            iterations: int = 1,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
    ) -> Generator[Dict, None, None]:
        """
        流式生成器 - 逐条产出，节省内存
        适用于大规模数据生成场景
        """
        unique_tracker = {f: set() for f in (unique_fields or [])}
        self._ext_data = foreign_keys or {}

        for i in range(iterations):
            self._context = {}
            record = self._generate_record(schema, unique_tracker)
            yield record

    def generate_chunks(
            self,
            schema: Dict,
            iterations: int = 1,
            chunk_size: int = 1000,
            unique_fields: Optional[List[str]] = None,
            foreign_keys: Optional[Dict] = None,
    ) -> Generator[List[Dict], None, None]:
        """
        分块生成器 - 每次产出一批数据
        适用于批量入库场景
        """
        chunk = []
        for record in self.generate_stream(schema, iterations, unique_fields, foreign_keys):
            chunk.append(record)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def _generate_record(
            self, schema: Dict, unique_tracker: Dict, path: str = "root"
    ) -> Dict:
        """生成单条记录"""
        record = {}

        for key, field_def in schema.items():
            current_path = f"{path}.{key}"

            try:
                value = self._generate_field(key, field_def, unique_tracker, current_path)
                record[key] = value
                self._context[key] = value  # 存入上下文供后续字段引用
            except Exception as e:
                raise SchemaError(
                    f"生成字段 '{key}' 失败: {str(e)}", path=current_path
                ) from e

        return record

    def _generate_field(
            self, key: str, field_def: Any, unique_tracker: Dict, path: str
    ) -> Any:
        """生成单个字段的值"""

        # ---------- 处理跨表外键关联 ----------
        if key in self._ext_data:
            ext_data, ext_field = self._ext_data[key]
            if isinstance(ext_data, list):
                source = ext_data
            else:
                source = ext_data.get(ext_field, [])
            return random.choice(source) if source else None

        # ---------- 处理字符串简写: "field": "{method}" ----------
        if isinstance(field_def, str):
            return self._resolve_string_field(field_def)

        # ---------- 处理字典定义 ----------
        if isinstance(field_def, dict):
            # 条件逻辑: if/then/else
            if 'if' in field_def:
                return self._generate_conditional(field_def, unique_tracker, path)

            # 引用其他字段: {'ref': 'user_id'}
            if 'ref' in field_def:
                ref_path = field_def['ref']
                return self._resolve_ref(ref_path)

            # 固定值列表: {'elements': [...], 'weights': [...]}
            if 'elements' in field_def:
                return self._generate_from_elements(field_def)

            # 表达式: {'expr': '${name}_${id}'}
            if 'expr' in field_def:
                return self._resolve_string_field(field_def['expr'])

            # 嵌套 schema
            if 'method' not in field_def:
                return self._generate_record(field_def, unique_tracker, path)

            # 标准 method 定义
            return self._generate_from_method(field_def, unique_tracker, key, path)

        # ---------- 处理列表定义 ----------
        if isinstance(field_def, list):
            # 取列表中的一个随机元素
            return random.choice(field_def)

        # ---------- 处理固定值 ----------
        return field_def

    def _resolve_string_field(self, pattern: str) -> Any:
        """
        解析字符串模式:
        - "{method}" -> 调用 faker method
        - "{seq:name:start:step}" -> 自增序列号
        - "{global:key}" -> 全局变量
        - "${field}" -> 引用上下文中的字段
        - "prefix_{method}_suffix" -> 混合模式
        """

        # 先解析字段引用 ${...}
        def replace_ref(match):
            ref_name = match.group(1)
            return str(self._resolve_ref(ref_name))

        pattern = self.REF_PATTERN.sub(replace_ref, pattern)

        # 解析 {seq:name:start:step} 序列号
        seq_match = re.match(r'^\{seq:(\w+)(?::(\d+))?(?::(\d+))?\}$', pattern)
        if seq_match:
            name = seq_match.group(1)
            start = int(seq_match.group(2)) if seq_match.group(2) else 1
            step = int(seq_match.group(3)) if seq_match.group(3) else 1
            from .context import parse_sequence_token
            from .fakerx import FakerX
            # 获取全局上下文中的序列号生成器
            import threading
            ctx = threading.local()
            if not hasattr(ctx, '_fakerx_instance'):
                ctx._fakerx_instance = None
            return self._get_sequence(name, start, step)

        # 解析 {global:key} 全局变量
        global_match = re.match(r'^\{global:(\w+)\}$', pattern)
        if global_match:
            key = global_match.group(1)
            from .fakerx import FakerX
            return self._get_global(key)

        # 再解析方法调用 {...}
        method_match = re.match(r'^\{(\w+)\}$', pattern)
        if method_match:
            # 纯方法调用: "{method}"
            method_name = method_match.group(1)
            return self._call_faker_method(method_name)

        # 混合模式: "prefix_{method}_suffix"
        def replace_method(match):
            method_name = match.group(1)
            return str(self._call_faker_method(method_name))

        result = re.sub(r'\{(\w+)\}', replace_method, pattern)
        return result

    def _get_sequence(self, name: str, start: int = 1, step: int = 1) -> int:
        """获取序列号的下一个值（通过 GenerationContext）"""
        if self._generation_context:
            return self._generation_context.sequence(name, start, step)
        # 回退：创建临时上下文
        from .context import GenerationContext
        ctx = GenerationContext()
        return ctx.sequence(name, start, step)

    def _get_global(self, key: str) -> Any:
        """获取全局变量值"""
        if self._generation_context:
            return self._generation_context.get_global(key)
        return None

    def _resolve_ref(self, ref_path: str) -> Any:
        """解析字段引用，支持点号嵌套: parent.child"""
        parts = ref_path.split('.')
        value = self._context
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise SchemaError(f"无法解析字段引用: {ref_path}")
        return value

    def _generate_conditional(
            self, field_def: Dict, unique_tracker: Dict, path: str
    ) -> Any:
        """
        条件逻辑生成:
        {
            'if': {'user_type': 'vip'},
            'then': {'method': 'pyfloat', 'min_value': 0.5, 'max_value': 0.8},
            'else': {'method': 'pyfloat', 'min_value': 0.9, 'max_value': 1.0}
        }
        """
        condition = field_def['if']
        then_def = field_def.get('then', {})
        else_def = field_def.get('else', {})

        # 评估条件
        matched = True
        for cond_key, cond_value in condition.items():
            actual = self._context.get(cond_key)
            if actual != cond_value:
                matched = False
                break

        chosen_def = then_def if matched else else_def
        return self._generate_field('', chosen_def, unique_tracker, path)

    def _generate_from_elements(self, field_def: Dict) -> Any:
        """从元素列表中随机选择，支持权重"""
        elements = field_def['elements']
        weights = field_def.get('weights')

        if weights:
            return random.choices(elements, weights=weights, k=1)[0]
        return random.choice(elements)

    def _generate_from_method(
            self,
            field_def: Dict,
            unique_tracker: Dict,
            key: str,
            path: str,
    ) -> Any:
        """通过 faker 方法生成值，支持参数和唯一性约束"""
        method_name = field_def['method']
        # 提取方法参数（排除特殊键）
        special_keys = {'method', 'if', 'then', 'else', 'ref', 'elements',
                        'weights', 'expr', 'unique', 'validate'}
        kwargs = {k: v for k, v in field_def.items() if k not in special_keys}

        # 解析参数中的字段引用
        kwargs = self._resolve_kwargs_refs(kwargs)

        is_unique = field_def.get('unique', key in unique_tracker)

        if is_unique and key in unique_tracker:
            return self._generate_unique(key, method_name, kwargs, unique_tracker)
        else:
            return self._call_faker_method(method_name, **kwargs)

    def _resolve_kwargs_refs(self, kwargs: Dict) -> Dict:
        """解析方法参数中的字段引用"""
        resolved = {}
        for k, v in kwargs.items():
            if isinstance(v, str) and self.REF_PATTERN.search(v):
                resolved[k] = self._resolve_ref(v[2:-1])
            else:
                resolved[k] = v
        return resolved

    def _generate_unique(
            self, key: str, method_name: str, kwargs: Dict, unique_tracker: Dict
    ) -> Any:
        """生成唯一值，最多重试100次"""
        seen = unique_tracker[key]
        max_retries = 100

        for _ in range(max_retries):
            value = self._call_faker_method(method_name, **kwargs)
            if value not in seen:
                seen.add(value)
                return value

        raise SchemaError(
            f"无法在 {max_retries} 次尝试内生成唯一值，"
            f"可能空间不足。字段: {key}, 已生成: {len(seen)} 条"
        )

    def _call_faker_method(self, method_name: str, **kwargs) -> Any:
        """安全调用 faker 方法"""
        method = getattr(self.faker, method_name, None)
        if method is None:
            raise SchemaError(
                f"未知的 faker 方法: '{method_name}'，"
                f"如果是自定义 provider，请确保已注册"
            )
        return method(**kwargs) if kwargs else method()
