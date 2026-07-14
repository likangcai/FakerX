# -*- coding: utf-8 -*-
"""Schema 生成器模块测试"""
import pytest
from fakerx import FakerX
from fakerx.schema import SchemaGenerator
from fakerx.exceptions import SchemaError


class TestSchemaGenerator:
    """SchemaGenerator 功能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)
        self.gen = SchemaGenerator(self.fake._faker)

    def test_string_method(self):
        result = self.gen._resolve_string_field('{name}')
        assert isinstance(result, str)

    def test_nested_schema(self):
        schema = {'user': {'name': '{name}', 'age': {'method': 'pyint'}}}
        result = self.gen.generate(schema, iterations=2)
        assert len(result) == 2
        assert 'user' in result[0]
        assert 'name' in result[0]['user']

    def test_elements_with_weights(self):
        schema = {'level': {'elements': ['A', 'B', 'C'], 'weights': [0.6, 0.3, 0.1]}}
        result = self.gen.generate(schema, iterations=100)
        values = [r['level'] for r in result]
        assert all(v in ['A', 'B', 'C'] for v in values)

    def test_conditional_logic(self):
        schema = {
            'type': {'elements': ['vip', 'normal']},
            'discount': {
                'if': {'type': 'vip'},
                'then': {'method': 'pyfloat', 'min_value': 0.5, 'max_value': 0.8},
                'else': {'method': 'pyfloat', 'min_value': 0.9, 'max_value': 1.0},
            }
        }
        result = self.gen.generate(schema, iterations=10)
        for r in result:
            if r['type'] == 'vip':
                assert 0.5 <= r['discount'] <= 0.8
            else:
                assert 0.9 <= r['discount'] <= 1.0

    def test_field_reference(self):
        schema = {'user_type': {'elements': ['vip', 'normal']}, 'profile': {'ref': 'user_type'}}
        from fakerx.context import GenerationContext
        gen = SchemaGenerator(self.fake._faker, context=GenerationContext())
        gen._context = {'user_type': 'vip'}
        result = gen._resolve_ref('user_type')
        assert result == 'vip'

    def test_unique_fields(self):
        schema = {'id': {'method': 'pyint', 'min_value': 1, 'max_value': 100}}
        result = self.gen.generate(schema, iterations=10, unique_fields=['id'])
        ids = [r['id'] for r in result]
        assert len(ids) == len(set(ids))  # 全部唯一

    def test_foreign_keys(self):
        ext_data = {'user_id': ([1, 2, 3], 'id')}
        schema = {'user_id': {'method': 'pyint'}}
        result = self.gen.generate(schema, iterations=5, foreign_keys=ext_data)
        for r in result:
            assert r['user_id'] in [1, 2, 3]

    def test_expr_field(self):
        schema = {'label': {'expr': 'User-${id}'}}
        gen = SchemaGenerator(self.fake._faker)
        gen._context = {'id': 42}
        result = gen._generate_field('label', {'expr': 'User-${id}'}, {}, 'root')
        assert result == 'User-42'

    def test_unknown_method(self):
        with pytest.raises(SchemaError):
            self.gen._call_faker_method('nonexistent_method')


class TestSchemaInFakerX:
    """FakerX 中的 Schema 集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_schema_with_post_process(self):
        schema = {'name': '{name}'}
        data = self.fake.schema(schema, iterations=3, post_process={'name': ['strip', 'title']})
        assert len(data) == 3

    def test_schema_stream(self):
        schema = {'id': '{pyint}'}
        count = sum(1 for _ in self.fake.schema_stream(schema, iterations=10))
        assert count == 10

    def test_schema_chunks(self):
        schema = {'id': '{pyint}'}
        chunks = list(self.fake.schema_chunks(schema, iterations=10, chunk_size=3))
        assert len(chunks) == 4  # 3+3+3+1

    def test_generate_relations(self):
        config = {
            'users': {'schema': {'id': '{pyint}'}, 'count': 3},
            'orders': {
                'schema': {'order_id': '{pyint}', 'user_id': {'method': 'pyint'}},
                'count': 5,
                'relations': {'user_id': 'users.id'}
            }
        }
        result = self.fake.generate_relations(config)
        assert len(result['users']) == 3
        assert len(result['orders']) == 5
        for order in result['orders']:
            assert order['user_id'] in [u['id'] for u in result['users']]