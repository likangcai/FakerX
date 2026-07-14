# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 14:48
# @Software  : PyCharm
# @FileName  : validators.py
# -----------------------------
"""
增强数据验证模块 - 类型检查、范围检查、正则匹配、跨字段验证、Pydantic 集成
"""

import re
from typing import Any, Dict, List, Optional, Callable, Type, Union
from dataclasses import dataclass, field


class ValidationRule:
    """验证规则基类"""
    def __init__(self, name: str = "", error_msg: str = ""):
        self.name = name
        self.error_msg = error_msg

    def validate(self, value: Any, record: Optional[Dict] = None) -> bool:
        raise NotImplementedError


@dataclass
class TypeRule(ValidationRule):
    """类型检查"""
    expected_type: Type = str
    name: str = "type_check"
    error_msg: str = "类型不匹配"

    def validate(self, value: Any, record=None) -> bool:
        if value is None:
            return True
        return isinstance(value, self.expected_type)


@dataclass
class RangeRule(ValidationRule):
    """范围检查"""
    min_value: Any = None
    max_value: Any = None
    name: str = "range_check"
    error_msg: str = "值超出范围"

    def validate(self, value: Any, record=None) -> bool:
        if value is None:
            return True
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


@dataclass
class LengthRule(ValidationRule):
    """长度检查"""
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    name: str = "length_check"
    error_msg: str = "长度不符合要求"

    def validate(self, value: Any, record=None) -> bool:
        if value is None:
            return True
        length = len(value)
        if self.min_len is not None and length < self.min_len:
            return False
        if self.max_len is not None and length > self.max_len:
            return False
        return True


@dataclass
class RegexRule(ValidationRule):
    """正则匹配"""
    pattern: str = ""
    name: str = "regex_check"
    error_msg: str = "格式不匹配"

    def validate(self, value: Any, record=None) -> bool:
        if value is None:
            return True
        return bool(re.match(self.pattern, str(value)))


@dataclass
class ChoiceRule(ValidationRule):
    """枚举值检查"""
    choices: List[Any] = field(default_factory=list)
    name: str = "choice_check"
    error_msg: str = "值不在允许的列表中"

    def validate(self, value: Any, record=None) -> bool:
        if value is None:
            return True
        return value in self.choices


@dataclass
class UniqueRule(ValidationRule):
    """唯一性检查（在批次内）"""
    name: str = "unique_check"
    error_msg: str = "值不唯一"
    _seen: set = field(default_factory=set, repr=False)

    def validate(self, value: Any, record=None) -> bool:
        if value in self._seen:
            return False
        self._seen.add(value)
        return True


@dataclass
class CrossFieldRule(ValidationRule):
    """跨字段验证"""
    other_field: str = ""
    operator: str = "eq"  # eq, ne, lt, le, gt, ge
    name: str = "cross_field_check"
    error_msg: str = "跨字段验证失败"

    def validate(self, value: Any, record: Optional[Dict] = None) -> bool:
        if record is None or self.other_field not in record:
            return True
        other_value = record[self.other_field]
        ops = {
            'eq': lambda a, b: a == b,
            'ne': lambda a, b: a != b,
            'lt': lambda a, b: a < b,
            'le': lambda a, b: a <= b,
            'gt': lambda a, b: a > b,
            'ge': lambda a, b: a >= b,
        }
        op_func = ops.get(self.operator, ops['eq'])
        return op_func(value, other_value)


@dataclass
class CustomRule(ValidationRule):
    """自定义验证函数"""
    func: Callable = None
    name: str = "custom_check"
    error_msg: str = "自定义验证失败"

    def validate(self, value: Any, record: Optional[Dict] = None) -> bool:
        if self.func is None:
            return True
        return self.func(value, record)


class SchemaValidator:
    """
    Schema 定义验证器

    验证 Schema 定义本身的合法性，检查：
    - method 是否存在
    - 参数是否合理（如 min_value < max_value）
    - 字段定义是否完整

    Example:
        >>> validator = SchemaValidator()
        >>> schema = {'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100}}
        >>> validator.validate(schema)
        True
    """

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, schema: Dict) -> bool:
        """
        验证 Schema 定义

        Returns:
            True 如果 schema 有效（有警告仍返回 True），否则 False
        """
        self.errors.clear()
        self.warnings.clear()

        if not isinstance(schema, dict):
            self.errors.append("Schema 必须是 dict")
            return False

        for key, field_def in schema.items():
            if isinstance(field_def, dict):
                if 'method' in field_def:
                    self._validate_method(key, field_def)
                elif 'elements' in field_def:
                    self._validate_elements(key, field_def)
                elif 'if' in field_def:
                    self._validate_conditional(key, field_def)
            elif isinstance(field_def, str):
                # 检查字符串模板 {method_name}
                import re
                m = re.match(r'^\{(\w+)\}$', field_def)
                if m:
                    method_name = m.group(1)
                    try:
                        from faker import Faker
                        fake = Faker('zh_CN')
                        if not hasattr(fake, method_name):
                            self.warnings.append(
                                f"字段 '{key}': 可能不存在的方法 '{method_name}'"
                            )
                    except Exception:
                        pass

        return len(self.errors) == 0

    def _validate_method(self, key: str, field_def: Dict):
        """验证 method 定义"""
        method_name = field_def['method']
        try:
            from faker import Faker
            fake = Faker('zh_CN')
            if not hasattr(fake, method_name):
                self.warnings.append(f"字段 '{key}': 可能不存在的方法 '{method_name}'")
        except Exception:
            pass

        # 检查范围参数
        min_val = field_def.get('min_value')
        max_val = field_def.get('max_value')
        if min_val is not None and max_val is not None and min_val > max_val:
            self.errors.append(
                f"字段 '{key}': min_value ({min_val}) 大于 max_value ({max_val})"
            )

    def _validate_elements(self, key: str, field_def: Dict):
        """验证 elements 定义"""
        elements = field_def.get('elements', [])
        if not elements:
            self.warnings.append(f"字段 '{key}': elements 列表为空")

        weights = field_def.get('weights')
        if weights and len(weights) != len(elements):
            self.errors.append(
                f"字段 '{key}': weights 长度 ({len(weights)}) 与 elements 长度 ({len(elements)}) 不匹配"
            )

    def _validate_conditional(self, key: str, field_def: Dict):
        """验证条件定义"""
        if 'then' not in field_def:
            self.errors.append(f"字段 '{key}': 条件块缺少 'then' 分支")
        if 'else' not in field_def:
            self.warnings.append(f"字段 '{key}': 条件块缺少 'else' 分支")

    def report(self) -> str:
        """生成验证报告"""
        lines = []
        if self.errors:
            lines.append("错误:")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.warnings:
            lines.append("警告:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if not self.errors and not self.warnings:
            lines.append("Schema 验证通过，无错误和警告")
        return "\n".join(lines)


class SchemaValidatorEnhanced:
    """
    增强版 Schema 验证器

    支持在 Schema 定义中直接嵌入验证规则，生成后自动验证。

    Example:
        >>> validator = SchemaValidatorEnhanced()
        >>> schema = {
        ...     'id': {
        ...         'method': 'pyint', 'min_value': 1,
        ...         'validate': [TypeRule(int), RangeRule(1, 9999)]
        ...     },
        ...     'email': {
        ...         'method': 'email',
        ...         'validate': [RegexRule(r'^[\w.]+@[\w.]+$')]
        ...     },
        ...     'start_date': {'method': 'date_this_year'},
        ...     'end_date': {
        ...         'method': 'date_this_year',
        ...         'validate': [CrossFieldRule('start_date', 'gt')]
        ...     }
        ... }
    """

    def __init__(self):
        self.errors: List[str] = []

    def validate_record(
            self,
            record: Dict,
            schema: Dict,
    ) -> List[str]:
        """
        验证单条记录是否符合 schema 中的验证规则

        Returns:
            错误信息列表，空列表表示通过
        """
        errors = []
        for field_name, field_def in schema.items():
            if not isinstance(field_def, dict):
                continue

            validate_rules = field_def.get('validate', [])
            if not validate_rules:
                continue

            value = record.get(field_name)
            for rule in validate_rules:
                if isinstance(rule, dict):
                    # 字典形式的规则定义
                    rule = self._build_rule_from_dict(rule)

                if rule and not rule.validate(value, record):
                    errors.append(
                        f"字段 '{field_name}' 验证失败: {rule.error_msg} "
                        f"(值: {value})"
                    )

        return errors

    def validate_records(
            self,
            records: List[Dict],
            schema: Dict,
    ) -> Dict[int, List[str]]:
        """
        批量验证记录

        Returns:
            {记录索引: [错误信息, ...]}
        """
        all_errors = {}
        for i, record in enumerate(records):
            errors = self.validate_record(record, schema)
            if errors:
                all_errors[i] = errors
        return all_errors

    def _build_rule_from_dict(self, rule_dict: Dict) -> Optional[ValidationRule]:
        """从字典构建验证规则"""
        rule_type = rule_dict.get('type', 'custom')

        builders = {
            'type': lambda d: TypeRule(
                expected_type=d.get('expected_type', str),
                error_msg=d.get('error_msg', '类型不匹配'),
            ),
            'range': lambda d: RangeRule(
                min_value=d.get('min'),
                max_value=d.get('max'),
                error_msg=d.get('error_msg', '值超出范围'),
            ),
            'length': lambda d: LengthRule(
                min_len=d.get('min'),
                max_len=d.get('max'),
                error_msg=d.get('error_msg', '长度不符合要求'),
            ),
            'regex': lambda d: RegexRule(
                pattern=d.get('pattern', ''),
                error_msg=d.get('error_msg', '格式不匹配'),
            ),
            'choice': lambda d: ChoiceRule(
                choices=d.get('choices', []),
                error_msg=d.get('error_msg', '值不在允许列表中'),
            ),
            'unique': lambda d: UniqueRule(
                error_msg=d.get('error_msg', '值不唯一'),
            ),
            'cross_field': lambda d: CrossFieldRule(
                other_field=d.get('field', ''),
                operator=d.get('operator', 'eq'),
                error_msg=d.get('error_msg', '跨字段验证失败'),
            ),
            'custom': lambda d: CustomRule(
                func=d.get('func'),
                error_msg=d.get('error_msg', '自定义验证失败'),
            ),
        }

        builder = builders.get(rule_type)
        return builder(rule_dict) if builder else None


# ----------------------------------------------------------------
# Pydantic 集成
# ----------------------------------------------------------------

def generate_pydantic_model(faker_instance, model_class, **overrides):
    """
    根据 Pydantic 模型生成数据

    自动解析模型字段类型并生成对应数据

    Example:
        >>> from pydantic import BaseModel, EmailStr, conint
        >>> class User(BaseModel):
        ...     id: conint(gt=0)
        ...     name: str
        ...     email: EmailStr
        ...     age: conint(ge=18, le=65)
        >>> user = generate_pydantic_model(fake, User)
    """
    try:
        # Pydantic v2
        from pydantic import TypeAdapter
        from pydantic.fields import FieldInfo
        model_fields = model_class.model_fields
    except (ImportError, AttributeError):
        # Pydantic v1
        model_fields = model_class.__fields__

    # 重试生成，最多 100 次
    import random as _random
    for attempt in range(100):
        data = {}
        for field_name, field_info in model_fields.items():
            if field_name in overrides:
                data[field_name] = overrides[field_name]
                continue

            # 获取字段类型信息
            try:
                # Pydantic v2
                annotation = field_info.annotation
                constraints = field_info.metadata or []
            except AttributeError:
                # Pydantic v1
                annotation = field_info.outer_type_
                constraints = []

            value = _generate_for_type(faker_instance, field_name, annotation, constraints)
            data[field_name] = value

        try:
            return model_class(**data)
        except Exception:
            if attempt == 99:
                raise
            continue

    raise RuntimeError(f"无法生成有效的 {model_class.__name__} 实例")


def _generate_for_type(faker_instance, field_name, annotation, constraints):
    """根据类型注解生成数据"""
    import datetime

    type_map = {
        str: lambda: getattr(faker_instance, 'pystr', lambda: 'str')(),
        int: lambda: getattr(faker_instance, 'pyint', lambda: 1)(),
        float: lambda: getattr(faker_instance, 'pyfloat', lambda: 1.0)(),
        bool: lambda: getattr(faker_instance, 'boolean', lambda: True)(),
        datetime.datetime: lambda: faker_instance.date_time_this_year(),
        datetime.date: lambda: faker_instance.date_this_year(),
        datetime.time: lambda: faker_instance.time(),
    }

    # 根据字段名智能推断
    name_lower = field_name.lower()
    if 'email' in name_lower:
        return faker_instance.email()
    elif 'name' in name_lower and 'user' not in name_lower:
        return faker_instance.name()
    elif 'username' in name_lower or 'user_name' in name_lower:
        return faker_instance.user_name()
    elif 'phone' in name_lower:
        return faker_instance.phone_number()
    elif 'address' in name_lower:
        return faker_instance.address()
    elif 'city' in name_lower:
        return faker_instance.city()
    elif 'url' in name_lower or 'link' in name_lower:
        return faker_instance.url()
    elif 'uuid' in name_lower:
        return faker_instance.uuid4()

    # 按类型生成
    for typ, gen_func in type_map.items():
        if annotation == typ:
            return gen_func()

    # 默认
    return faker_instance.pystr()
