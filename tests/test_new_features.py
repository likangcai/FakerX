# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:04
# @Software  : PyCharm
# @FileName  : test_new_features.py
# -----------------------------
"""
FakerX 新功能测试
"""

import pytest
import os
import tempfile
from fakerx import FakerX, SchemaError


class TestSchemaFieldReference:
    """测试字段引用功能"""

    def setup_method(self):
        self.fake = FakerX()

    def test_field_reference(self):
        """同记录内字段引用"""
        schema = {
            'user_id': {'method': 'pyint', 'min_value': 1, 'max_value': 100},
            'profile': {
                'ref_user_id': {'ref': 'user_id'},
                'display_name': {'expr': 'User_${user_id}'}
            }
        }
        data = self.fake.schema(schema, iterations=5)
        for record in data:
            assert record['profile']['ref_user_id'] == record['user_id']
            assert f"User_{record['user_id']}" == record['profile']['display_name']


class TestConditionalLogic:
    """测试条件逻辑"""

    def setup_method(self):
        self.fake = FakerX()

    def test_conditional_generation(self):
        """if/then/else 条件生成"""
        schema = {
            'user_type': {'elements': ['vip', 'normal']},
            'discount': {
                'if': {'user_type': 'vip'},
                'then': {'method': 'pyfloat', 'min_value': 0.5, 'max_value': 0.8},
                'else': {'method': 'pyfloat', 'min_value': 0.9, 'max_value': 1.0}
            }
        }
        data = self.fake.schema(schema, iterations=50)
        for record in data:
            if record['user_type'] == 'vip':
                assert 0.5 <= record['discount'] <= 0.8
            else:
                assert 0.9 <= record['discount'] <= 1.0


class TestForeignKeys:
    """测试跨表关联"""

    def setup_method(self):
        self.fake = FakerX()

    def test_foreign_key(self):
        """外键关联"""
        users = self.fake.schema(
            {'id': {'method': 'pyint', 'min_value': 1, 'max_value': 1000}},
            iterations=10
        )
        user_ids = [u['id'] for u in users]

        orders = self.fake.schema(
            {
                'order_id': {'method': 'pyint', 'min_value': 1},
                'user_id': {'method': 'pyint'}  # 会被 foreign_keys 覆盖
            },
            iterations=30,
            foreign_keys={'user_id': (user_ids, 'id')}
        )

        for order in orders:
            assert order['user_id'] in user_ids

    def test_generate_relations(self):
        """多表关联生成"""
        config = {
            'users': {
                'schema': {'id': {'method': 'pyint', 'min_value': 1}},
                'count': 5
            },
            'orders': {
                'schema': {
                    'order_id': {'method': 'pyint', 'min_value': 1},
                    'user_id': {'method': 'pyint'}
                },
                'count': 20,
                'relations': {'user_id': 'users.id'}
            }
        }
        data = self.fake.generate_relations(config)
        user_ids = [u['id'] for u in data['users']]

        assert len(data['users']) == 5
        assert len(data['orders']) == 20
        for order in data['orders']:
            assert order['user_id'] in user_ids


class TestStreamingGeneration:
    """测试流式生成"""

    def setup_method(self):
        self.fake = FakerX()

    def test_schema_stream(self):
        """流式生成器"""
        schema = {'id': {'method': 'pyint', 'min_value': 1}}
        gen = self.fake.schema_stream(schema, iterations=100)
        count = sum(1 for _ in gen)
        assert count == 100

    def test_schema_chunks(self):
        """分块生成"""
        schema = {'id': {'method': 'pyint'}}
        chunks = list(self.fake.schema_chunks(
            schema, iterations=100, chunk_size=30
        ))
        assert len(chunks) == 4  # 30 + 30 + 30 + 10
        assert len(chunks[0]) == 30
        assert len(chunks[-1]) == 10

    def test_csv_stream_export(self):
        """流式 CSV 导出"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}
        gen = self.fake.schema_stream(schema, iterations=1000)

        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.csv', delete=False
        ) as f:
            filepath = f.name

        try:
            self.fake.to_csv_stream(gen, filepath)
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 1001  # header + 1000 rows
        finally:
            os.unlink(filepath)


class TestTemplates:
    """测试模板系统"""

    def setup_method(self):
        self.fake = FakerX()

    def test_builtin_template(self):
        """内置模板"""
        users = self.fake.template('user', count=5)
        assert len(users) == 5
        for user in users:
            assert 'id' in user
            assert 'username' in user
            assert 'email' in user
            assert user['status'] in ['active', 'inactive', 'banned']

    def test_template_extend(self):
        """模板扩展"""
        users = self.fake.template('user', count=3, extend={
            'level': {'elements': ['bronze', 'silver', 'gold']}
        })
        for user in users:
            assert user['level'] in ['bronze', 'silver', 'gold']

    def test_template_override(self):
        """模板覆盖"""
        users = self.fake.template('user', count=10, override={
            'status': {'elements': ['active']}
        })
        for user in users:
            assert user['status'] == 'active'

    def test_custom_template(self):
        """自定义模板"""
        self.fake.register_template('my_model', {
            'id': {'method': 'pyint'},
            'name': '{name}'
        }, description='我的自定义模型')

        data = self.fake.template('my_model', count=3)
        assert len(data) == 3

    def test_list_templates(self):
        """列出模板"""
        templates = self.fake.list_templates()
        assert 'user' in templates
        assert 'product' in templates
        assert 'order' in templates


class TestAnonymizer:
    """测试数据脱敏"""

    def setup_method(self):
        self.fake = FakerX()

    def test_phone_anonymize(self):
        assert self.fake.anonymize('13812345678', 'phone') == '138****5678'

    def test_email_anonymize(self):
        result = self.fake.anonymize('zhangsan@gmail.com', 'email')
        assert result.startswith('z')
        assert '@gmail.com' in result
        assert '*' in result

    def test_id_card_anonymize(self):
        result = self.fake.anonymize('110101199001011234', 'id_card')
        assert result.startswith('110101')
        assert result.endswith('1234')
        assert '********' in result

    def test_auto_detect(self):
        """自动识别类型"""
        assert '*' in self.fake.anonymize('13812345678')
        assert '@' in self.fake.anonymize('test@example.com')

    def test_anonymize_dict(self):
        data = {'name': '张三', 'phone': '13812345678', 'email': 'a@b.com'}
        result = self.fake.anonymize_dict(
            data, {'phone': 'phone', 'email': 'email', 'name': 'name'}
        )
        assert result['name'] == '张*'
        assert '****' in result['phone']
        assert result['email'] != 'a@b.com'


class TestSchemaValidator:
    """测试 Schema 验证"""

    def setup_method(self):
        self.fake = FakerX()

    def test_valid_schema(self):
        schema = {
            'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100},
            'name': '{name}',
        }
        assert self.fake.validate_schema(schema) is True

    def test_invalid_min_max(self):
        schema = {
            'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50}
        }
        assert self.fake.validate_schema(schema) is False

    def test_elements_weights_mismatch(self):
        schema = {
            'level': {'elements': ['A', 'B'], 'weights': [0.5, 0.3, 0.2]}
        }
        assert self.fake.validate_schema(schema) is False


class TestCustomProvider:
    """测试自定义 Provider"""

    def setup_method(self):
        self.fake = FakerX()

    def test_register_provider(self):
        @self.fake.register_provider('phone_cn')
        def gen_phone(fake, **kw):
            prefixes = ['138', '139', '150', '188']
            prefix = fake.random_element(prefixes)
            return prefix + ''.join(
                str(fake.random_digit()) for _ in range(8)
            )

        data = self.fake.schema({'phone': '{phone_cn}'}, iterations=5)
        for record in data:
            assert record['phone'].startswith(('138', '139', '150', '188'))
            assert len(record['phone']) == 11
