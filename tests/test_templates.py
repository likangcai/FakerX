# -*- coding: utf-8 -*-
"""预设模板模块测试"""
import json
import os
import tempfile
import pytest
from fakerx.templates import TemplateRegistry, BUILTIN_TEMPLATES
from fakerx.exceptions import TemplateNotFoundError


class TestTemplateRegistry:
    """TemplateRegistry 功能测试"""

    def setup_method(self):
        self.registry = TemplateRegistry()

    def test_builtin_templates_exist(self):
        for name in ['user', 'product', 'order', 'article', 'log']:
            assert name in BUILTIN_TEMPLATES

    def test_get_builtin_template(self):
        tmpl = self.registry.get('user')
        assert 'schema' in tmpl
        assert 'description' in tmpl
        assert 'username' in tmpl['schema']

    def test_get_schema(self):
        schema = self.registry.get_schema('user')
        assert 'username' in schema
        assert 'email' in schema
        assert 'id' in schema

    def test_template_not_found(self):
        with pytest.raises(TemplateNotFoundError):
            self.registry.get('nonexistent')

    def test_get_schema_with_extend(self):
        schema = self.registry.get_schema('user', extend={'extra_field': '{pyint}'})
        assert 'extra_field' in schema
        assert 'username' in schema  # 原有字段保留

    def test_get_schema_with_override(self):
        schema = self.registry.get_schema('user', override={'username': '{email}'})
        assert schema['username'] == '{email}'

    def test_register_custom_template(self):
        custom = {'fields': {'id': '{pyint}'}}
        self.registry.register('custom', custom, '自定义模板')
        assert self.registry.get('custom')['schema'] == custom
        assert 'custom' in self.registry.list_templates()

    def test_remove_custom_template(self):
        self.registry.register('temp', {'id': '{pyint}'})
        assert 'temp' in self.registry.list_templates()
        self.registry.remove('temp')
        assert 'temp' not in self.registry.list_templates()

    def test_cannot_remove_builtin(self):
        with pytest.raises(ValueError):
            self.registry.remove('user')

    def test_list_templates(self):
        templates = self.registry.list_templates()
        assert 'user' in templates
        assert 'product' in templates
        assert 'order' in templates

    def test_load_from_json_file(self):
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump({'name': 'test_tmpl', 'schema': {'id': '{pyint}'}}, f)
            filepath = f.name

        try:
            self.registry.load_from_file(filepath)
            assert 'test_tmpl' in self.registry.list_templates()
        finally:
            os.remove(filepath)


class TestBuiltinTemplates:
    """内置模板验证"""

    def setup_method(self):
        self.registry = TemplateRegistry()

    def test_user_template_structure(self):
        schema = self.registry.get_schema('user')
        for field in ['id', 'username', 'email', 'phone', 'created_at', 'status']:
            assert field in schema, f"user 模板缺少字段: {field}"

    def test_product_template_structure(self):
        schema = self.registry.get_schema('product')
        for field in ['id', 'name', 'price', 'stock', 'category', 'sku']:
            assert field in schema

    def test_order_template_structure(self):
        schema = self.registry.get_schema('order')
        for field in ['order_id', 'user_id', 'total_amount', 'status', 'created_at']:
            assert field in schema

    def test_article_template_structure(self):
        schema = self.registry.get_schema('article')
        for field in ['id', 'title', 'content', 'author', 'tags', 'views']:
            assert field in schema

    def test_log_template_structure(self):
        schema = self.registry.get_schema('log')
        for field in ['timestamp', 'level', 'message', 'service', 'request_id']:
            assert field in schema