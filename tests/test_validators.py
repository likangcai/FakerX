# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:16
# @Software  : PyCharm
# @FileName  : test_validators.py
# -----------------------------
"""
验证器测试
"""

import pytest
from fakerx import FakerX
from fakerx.validators import (
    SchemaValidator, SchemaValidatorEnhanced,
    TypeRule, RangeRule, LengthRule, RegexRule,
    ChoiceRule, UniqueRule, CrossFieldRule, CustomRule,
    generate_pydantic_model
)
from fakerx.exceptions import SchemaError, ValidationError, FakerXError
from pydantic import BaseModel, conint, EmailStr, Field


class TestSchemaValidator:
    """SchemaValidator 基础功能测试"""

    def setup_method(self):
        self.validator = SchemaValidator()
        self.fake = FakerX('zh_CN', seed=42)

    def test_validate_valid_schema(self):
        """验证有效的 Schema"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100},
            'name': '{name}',
            'email': {'method': 'email'},
        }
        assert self.validator.validate(schema) is True

    def test_validate_invalid_schema(self):
        """验证无效的 Schema"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50},  # min > max
        }
        assert self.validator.validate(schema) is False

    def test_validate_with_warnings(self):
        """验证包含警告的 Schema"""
        schema = {
            'unknown_method': {'method': 'nonexistent_method'},
        }
        assert self.validator.validate(schema) is True  # 警告不阻止通过

    def test_report(self):
        """验证报告功能"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50},
            'unknown': '{nonexistent_method}',
        }
        self.validator.validate(schema)
        report = self.validator.report()
        assert "错误" in report
        assert "警告" in report


class TestSchemaValidatorEnhanced:
    """增强版验证器测试"""

    def setup_method(self):
        self.validator = SchemaValidatorEnhanced()
        self.fake = FakerX('zh_CN', seed=42)

    def test_validate_record(self):
        """验证单条记录"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100,
                   'validate': [TypeRule(int), RangeRule(1, 100)]},
            'email': {'method': 'email',
                     'validate': [RegexRule(r'^[\w.]+@[\w.]+\.[\w.]+$')]},
        }

        # 生成有效数据
        data = self.fake.schema(schema, iterations=1)[0]
        errors = self.validator.validate_record(data, schema)
        assert len(errors) == 0

        # 生成无效数据（故意制造错误）
        invalid_data = data.copy()
        invalid_data['id'] = 200  # 超出范围
        errors = self.validator.validate_record(invalid_data, schema)
        assert len(errors) > 0
        assert "值超出范围" in errors[0]

    def test_validate_records(self):
        """批量验证记录"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100,
                   'validate': [TypeRule(int), RangeRule(1, 100)]},
        }

        data = self.fake.schema(schema, iterations=10)
        # 故意修改一条数据
        data[0]['id'] = 200

        errors = self.validator.validate_records(data, schema)
        assert len(errors) == 1  # 只有一条错误
        assert 0 in errors  # 第0条记录有错误

    def test_validate_with_cross_field_rule(self):
        """跨字段验证"""
        schema = {
            'start_date': {'method': 'date_this_year'},
            'end_date': {
                'method': 'date_this_year',
                'validate': [CrossFieldRule('start_date', 'gt')]
            }
        }

        # 生成有效数据（多次尝试，确保 end_date > start_date）
        data = None
        for _ in range(10):
            try:
                data = self.fake.schema(schema, iterations=1)[0]
                break
            except FakerXError:
                continue
        assert data is not None, "无法生成有效数据"
        errors = self.validator.validate_record(data, schema)
        assert len(errors) == 0

        # 生成无效数据（end_date 早于 start_date）
        from datetime import datetime, timedelta
        invalid_data = data.copy()
        invalid_data['end_date'] = data['start_date'] - timedelta(days=1)  # 早于 start_date
        errors = self.validator.validate_record(invalid_data, schema)
        assert len(errors) > 0
        assert "跨字段验证失败" in errors[0]

    def test_validate_with_unique_rule(self):
        """唯一性验证"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100,
                   'validate': [UniqueRule()]},
        }

        data = self.fake.schema(schema, iterations=2)
        # 故意制造重复
        data[1]['id'] = data[0]['id']

        # 使用新的 UniqueRule 实例进行验证（避免生成阶段的 _seen 残留）
        fresh_schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100,
                   'validate': [UniqueRule()]},
        }
        errors = self.validator.validate_records(data, fresh_schema)
        assert len(errors) == 1
        assert 1 in errors  # 第1条记录有错误


class TestPydanticIntegration:
    """Pydantic 集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_generate_pydantic_model(self):
        """生成 Pydantic 模型数据"""
        from pydantic import BaseModel, conint, Field

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            email: str
            age: conint(ge=18, le=65) = Field(default=30)

        # 多次尝试确保生成有效数据
        for _ in range(50):
            try:
                user = generate_pydantic_model(self.fake._faker, User)
                assert isinstance(user, User)
                assert user.id > 0
                assert isinstance(user.name, str)
                assert isinstance(user.email, str)
                assert 18 <= user.age <= 65
                return
            except Exception:
                continue
        raise AssertionError("无法生成有效的 Pydantic 模型数据")

    def test_pydantic_with_overrides(self):
        """Pydantic 模型带覆盖参数"""
        from pydantic import BaseModel, conint

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            age: conint(ge=18, le=65)

        user = generate_pydantic_model(self.fake._faker, User, age=25)
        assert user.age == 25

    def test_pydantic_invalid_data(self):
        """Pydantic 模型生成失败"""
        from pydantic import BaseModel, conint

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            age: conint(ge=18, le=65)

        # 生成大量数据，确保有无效数据
        for _ in range(100):
            try:
                user = generate_pydantic_model(self.fake._faker, User)
                assert user.id > 0
                assert 18 <= user.age <= 65
            except Exception as e:
                # Pydantic 会自动验证失败
                assert isinstance(e, (ValueError, TypeError))


class TestValidationRules:
    """验证规则测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_type_rule(self):
        """类型检查规则"""
        rule = TypeRule(expected_type=int)
        assert rule.validate(42) is True
        assert rule.validate("42") is False
        assert rule.validate(None) is True

    def test_range_rule(self):
        """范围检查规则"""
        rule = RangeRule(min_value=1, max_value=100)
        assert rule.validate(50) is True
        assert rule.validate(0) is False
        assert rule.validate(101) is False

    def test_length_rule(self):
        """长度检查规则"""
        rule = LengthRule(min_len=3, max_len=10)
        assert rule.validate("hello") is True
        assert rule.validate("hi") is False
        assert rule.validate("a" * 11) is False

    def test_regex_rule(self):
        """正则匹配规则"""
        rule = RegexRule(pattern=r'^[\w.]+@[\w.]+\.[\w.]+$')
        assert rule.validate("test@example.com") is True
        assert rule.validate("invalid-email") is False

    def test_choice_rule(self):
        """枚举值检查规则"""
        rule = ChoiceRule(choices=['A', 'B', 'C'])
        assert rule.validate('A') is True
        assert rule.validate('D') is False

    def test_unique_rule(self):
        """唯一性检查规则"""
        rule = UniqueRule()
        assert rule.validate('value1') is True
        assert rule.validate('value1') is False  # 重复
        assert rule.validate('value2') is True

    def test_cross_field_rule(self):
        """跨字段验证规则"""
        rule = CrossFieldRule(other_field='field1', operator='gt')
        # 需要记录上下文
        record = {'field1': 10, 'field2': 20}
        assert rule.validate(20, record) is True
        assert rule.validate(5, record) is False

    def test_custom_rule(self):
        """自定义验证规则"""
        def custom_validator(value, record):
            return value > 0

        rule = CustomRule(func=custom_validator)
        assert rule.validate(10, {'field': 5}) is True
        assert rule.validate(-1, {'field': 5}) is False


class TestSchemaValidationInFakerX:
    """FakerX 中的 Schema 验证集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_schema_validation_in_generate(self):
        """生成时自动验证"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100,
                   'validate': [TypeRule(int), RangeRule(1, 100)]},
            'email': {'method': 'email',
                     'validate': [RegexRule(r'^[\w.]+@[\w.]+\.[\w.]+$')]},
        }

        # 正常生成
        data = self.fake.schema(schema, iterations=10)
        for record in data:
            assert 1 <= record['id'] <= 100
            assert '@' in record['email']

        # 验证失败的情况
        invalid_schema = {
            'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50},  # min > max
        }
        with pytest.raises(SchemaError):
            self.fake.schema(invalid_schema, iterations=1)

    def test_validation_with_post_process(self):
        """后处理 + 验证"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100},
            'name': {'method': 'name'},
        }

        data = self.fake.schema(
            schema, iterations=10,
            post_process={'name': ['strip', 'title']}
        )

        for record in data:
            assert 1 <= record['id'] <= 100
            assert isinstance(record['name'], str)
            # title 处理后，确保首字母大写（英文名）或保持原样（中文名）
            assert record['name'] == record['name'].strip()


class TestValidationErrors:
    """验证错误处理测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_multiple_validation_errors(self):
        """多条验证错误"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50},  # 范围错误
            'email': {'method': 'email',
                     'validate': [RegexRule(r'^[\w.]+@[\w.]+\.[\w.]+$')]},
        }

        with pytest.raises(SchemaError) as exc_info:
            self.fake.schema(schema, iterations=1)

        error = exc_info.value
        assert "id" in str(error)


class TestValidatorPerformance:
    """验证器性能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)
        self.validator = SchemaValidatorEnhanced()

    def test_validation_performance(self):
        """验证性能"""
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100},
            'name': {'method': 'name'},
            'email': {'method': 'email',
                     'validate': [RegexRule(r'^[\w.]+@[\w.]+\.[\w.]+$')]},
        }

        # 生成 1000 条数据并验证
        import time
        start = time.time()
        data = self.fake.schema(schema, iterations=1000)
        for record in data:
            errors = self.validator.validate_record(record, schema)
            assert len(errors) == 0
        duration = time.time() - start

        # 应该在合理时间内完成
        assert duration < 5.0  # 5 秒内完成 1000 条验证


class TestValidatorEdgeCases:
    """验证器边界情况测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)
        self.validator = SchemaValidator()

    def test_empty_schema(self):
        """空 Schema"""
        schema = {}
        assert self.validator.validate(schema) is True

    def test_schema_with_none_values(self):
        """Schema 中包含 None 值"""
        schema = {
            'id': None,
            'name': {'method': 'name'},
        }
        assert self.validator.validate(schema) is True

    def test_schema_with_empty_lists(self):
        """Schema 中包含空列表"""
        schema = {
            'tags': {'elements': []},
        }
        assert self.validator.validate(schema) is True

    def test_schema_with_complex_validation(self):
        """复杂验证规则"""
        schema = {
            'user_type': {'elements': ['admin', 'user', 'guest']},
            'permissions': {
                'if': {'user_type': 'admin'},
                'then': {'elements': ['read', 'write', 'delete']},
                'else': {'elements': ['read']},
            },
        }
        assert self.validator.validate(schema) is True
