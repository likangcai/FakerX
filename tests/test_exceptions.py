# -*- coding: utf-8 -*-
"""自定义异常模块测试"""
import pytest
from fakerx.exceptions import (
    FakerXError, SchemaError, ValidationError,
    TemplateNotFoundError, ProviderError,
)


class TestFakerXError:
    """FakerXError 基础异常测试"""

    def test_base_exception(self):
        err = FakerXError("基础错误")
        assert str(err) == "基础错误"
        assert isinstance(err, Exception)

    def test_schema_error_with_path(self):
        err = SchemaError("字段错误", path="root.id")
        assert "[root.id] 字段错误" in str(err)

    def test_schema_error_without_path(self):
        err = SchemaError("字段错误")
        assert str(err) == "字段错误"

    def test_validation_error(self):
        err = ValidationError("验证失败")
        assert str(err) == "验证失败"
        assert isinstance(err, FakerXError)

    def test_template_not_found(self):
        err = TemplateNotFoundError("模板不存在")
        assert str(err) == "模板不存在"
        assert isinstance(err, FakerXError)

    def test_provider_error(self):
        err = ProviderError("Provider 错误")
        assert str(err) == "Provider 错误"
        assert isinstance(err, FakerXError)

    def test_inheritance_chain(self):
        """验证异常继承链"""
        assert issubclass(SchemaError, FakerXError)
        assert issubclass(ValidationError, FakerXError)
        assert issubclass(TemplateNotFoundError, FakerXError)
        assert issubclass(ProviderError, FakerXError)
        assert issubclass(FakerXError, Exception)