# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:49
# @Software  : PyCharm
# @FileName  : test_providers.py
# -----------------------------
"""
Provider 测试
"""

import pytest
from fakerx import FakerX
from fakerx.providers import ProviderRegistry, register_provider, \
    list_providers, get_provider_instance
from fakerx.exceptions import ProviderError
from faker.providers import BaseProvider


class TestProviderRegistry:
    """Provider 注册中心测试"""

    def setup_method(self):
        self.registry = ProviderRegistry()

    def test_register_provider(self):
        """注册 Provider"""

        class TestProvider(BaseProvider):
            def test_method(self):
                return "test_value"

        self.registry.register('test_provider', TestProvider)

        assert self.registry.has_provider('test_provider')
        assert self.registry.get_provider('test_provider') == TestProvider

    def test_register_instance(self):
        """注册 Provider 实例"""

        class TestProvider(BaseProvider):
            def test_method(self):
                return "test_value"

        from faker import Faker
        instance = TestProvider(Faker('zh_CN'))
        self.registry.register_instance('test_instance', instance)

        assert self.registry.get_provider_instance('test_instance') == instance

    def test_get_provider_instance(self):
        """获取 Provider 实例"""

        class TestProvider(BaseProvider):
            def test_method(self):
                return "test_value"

        self.registry.register('test_provider', TestProvider)

        instance = self.registry.get_provider_instance('test_provider')
        assert isinstance(instance, TestProvider)
        assert instance.test_method() == "test_value"

    def test_dependencies(self):
        """依赖解析"""

        class ProviderA(BaseProvider):
            pass

        class ProviderB(BaseProvider):
            pass

        class ProviderC(BaseProvider):
            pass

        self.registry.register('a', ProviderA)
        self.registry.register('b', ProviderB, dependencies=['a'])
        self.registry.register('c', ProviderC, dependencies=['b', 'a'])

        resolved = self.registry.resolve_dependencies('c')
        assert 'a' in resolved
        assert 'b' in resolved
        assert len(resolved) == 2

    def test_validate_dependencies(self):
        """依赖验证"""

        class ProviderA(BaseProvider):
            pass

        class ProviderB(BaseProvider):
            pass

        self.registry.register('a', ProviderA)

        # 注册依赖未注册的 Provider
        self.registry.register('b', ProviderB, dependencies=['c'])
        # validate_dependencies 应该捕获这个错误
        with pytest.raises(ProviderError):
            self.registry.validate_dependencies()

    def test_global_registry(self):
        """全局注册中心"""

        class TestProvider(BaseProvider):
            def test_method(self):
                return "global_value"

        register_provider('global_test', TestProvider)

        assert 'global_test' in list_providers()
        instance = get_provider_instance('global_test')
        assert instance.test_method() == "global_value"


class TestCustomProviderIntegration:
    """自定义 Provider 集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_register_provider_function(self):
        """注册 Provider 函数"""

        def gen_test_method(faker, **kw):
            return "custom_value"

        self.fake.register_provider('test_method', gen_test_method)

        result = self.fake.test_method()
        assert result == "custom_value"

    def test_register_provider_in_schema(self):
        """Schema 中使用自定义 Provider"""

        def gen_custom_id(faker, **kw):
            return f"CUST-{faker.pyint(min_value=1, max_value=1000)}"

        self.fake.register_provider('custom_id', gen_custom_id)

        data = self.fake.schema({
            'id': '{custom_id}'
        }, iterations=3)

        for record in data:
            assert record['id'].startswith('CUST-')
            assert '-' in record['id']

    def test_add_provider_class(self):
        """添加 Provider 类"""

        class CustomProvider(BaseProvider):
            def custom_name(self):
                return f"Custom-{self.random_element(['A', 'B', 'C'])}"

        self.fake.add_provider(CustomProvider)

        result = self.fake.custom_name()
        assert result.startswith('Custom-')
        assert result.split('-')[1] in ['A', 'B', 'C']

    def test_provider_in_schema(self):
        """Schema 中使用 Provider 类方法"""

        class CustomProvider(BaseProvider):
            def custom_name(self):
                return f"Custom-{self.random_element(['A', 'B', 'C'])}"

        self.fake.add_provider(CustomProvider)

        data = self.fake.schema({
            'name': '{custom_name}'
        }, iterations=5)

        for record in data:
            assert record['name'].startswith('Custom-')
            assert record['name'].split('-')[1] in ['A', 'B', 'C']
