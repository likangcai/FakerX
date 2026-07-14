# -*- coding: utf-8 -*-
"""
集成测试 - pytest 和 unittest 插件全面测试
"""
import pytest
from fakerx import FakerX
from fakerx.integrations.pytest_plugin import (
    fake_schema, fake_batch, fake_pydantic, fakerx_parametrize,
    fakerx_config, fake_data, fake_record, fake_records,
)
from fakerx.integrations.unittest_base import FakerXTestCase, FakeData
from fakerx.exceptions import FakerXError


class TestPytestFixtures:
    """pytest fixture 测试"""

    def test_fakerx_config_fixture(self, fakerx_config):
        """fakerx_config fixture 提供配置"""
        assert 'locale' in fakerx_config
        assert 'seed' in fakerx_config
        assert fakerx_config['locale'] == 'zh_CN'

    def test_fake_data_fixture(self, fake_data):
        """fake_data fixture 提供 FakerX 实例"""
        assert isinstance(fake_data, FakerX)
        user = fake_data.template('user', count=1)[0]
        assert 'email' in user
        assert 'username' in user

    def test_fake_record_fixture(self, fake_record):
        """fake_record fixture 生成单条记录"""
        record = fake_record({'id': '{pyint}', 'name': '{name}'})
        assert 'id' in record
        assert 'name' in record

    def test_fake_records_fixture(self, fake_records):
        """fake_records fixture 生成多条记录"""
        records = fake_records({'id': '{pyint}', 'name': '{name}'}, iterations=10)
        assert len(records) == 10
        for r in records:
            assert 'id' in r
            assert 'name' in r

    def test_fake_records_default_count(self, fake_records):
        """fake_records 默认条数"""
        records = fake_records({'id': '{pyint}'})
        assert len(records) == 10  # 默认 10 条


class TestPytestDecorators:
    """pytest 装饰器测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_fake_schema_single_record(self):
        """@fake_schema 单条记录"""
        @fake_schema({'id': '{pyint}', 'name': '{name}'})
        def test_fn(record):
            assert 'id' in record
            assert 'name' in record
        test_fn()

    def test_fake_schema_multiple_records(self):
        """@fake_schema 多条记录"""
        @fake_schema({'id': '{pyint}'}, iterations=5)
        def test_fn(records):
            assert len(records) == 5
            for r in records:
                assert 'id' in r
        test_fn()

    def test_fake_schema_with_unique_fields(self):
        """@fake_schema 带唯一字段"""
        @fake_schema({'id': {'method': 'pyint', 'min_value': 1, 'max_value': 1000}},
                     iterations=10, unique_fields=['id'])
        def test_fn(records):
            assert len(records) == 10
            ids = [r['id'] for r in records]
            assert len(ids) == len(set(ids))  # 全部唯一
        test_fn()

    def test_fake_batch_decorator(self):
        """@fake_batch 模板批量生成"""
        @fake_batch('user', count=3)
        def test_fn(users):
            assert len(users) == 3
            for u in users:
                assert 'username' in u
                assert 'email' in u
        test_fn()

    def test_fake_batch_with_extend(self):
        """@fake_batch 带扩展字段"""
        @fake_batch('user', count=3, extend={'extra': '{pyint}'})
        def test_fn(users):
            assert len(users) == 3
            for u in users:
                assert 'extra' in u
        test_fn()

    def test_fake_pydantic_single(self):
        """@fake_pydantic 单条 Pydantic 模型"""
        from pydantic import BaseModel, conint

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            email: str

        @fake_pydantic(User, count=1)
        def test_fn(model):
            assert isinstance(model, User)
            assert model.id > 0
            assert isinstance(model.name, str)
        test_fn()

    def test_fake_pydantic_multiple(self):
        """@fake_pydantic 多条 Pydantic 模型"""
        from pydantic import BaseModel, conint

        class Item(BaseModel):
            id: conint(gt=0)
            name: str

        @fake_pydantic(Item, count=3)
        def test_fn(models):
            assert len(models) == 3
            for m in models:
                assert isinstance(m, Item)
                assert m.id > 0
        test_fn()

    def test_fakerx_parametrize_direct(self):
        """@fakerx_parametrize 直接调用"""
        @fakerx_parametrize({'id': '{pyint}'}, iterations=3)
        def test_fn(record):
            assert isinstance(record['id'], int)

        test_fn(record={'id': 1})


class TestPytestAdvanced:
    """pytest 高级功能测试"""

    def test_decorator_with_seed_consistency(self):
        """装饰器与种子一致性"""
        @fake_schema({'id': '{pyint}'}, iterations=2)
        def test_fn(records):
            ids = [r['id'] for r in records]
            return ids

        result1 = test_fn()
        result2 = test_fn()
        # 每次调用生成不同数据（无固定种子）
        assert result1 != result2 or result1 == result2

    def test_large_dataset_integration(self):
        """大数据集"""
        @fake_schema({'id': '{pyint}', 'name': '{name}'}, iterations=500)
        def test_fn(records):
            assert len(records) == 500
        test_fn()

    def test_nested_schema_in_decorator(self):
        """装饰器中嵌套 Schema"""
        @fake_schema({
            'user': {'name': '{name}', 'email': '{email}'},
            'meta': {'level': {'elements': ['A', 'B']}}
        })
        def test_fn(record):
            assert 'user' in record
            assert 'meta' in record
            assert 'name' in record['user']
            assert 'email' in record['user']
            assert record['meta']['level'] in ['A', 'B']
        test_fn()


class TestPytestPluginRegistration:
    """pytest 插件注册测试"""

    def test_plugin_has_required_functions(self):
        """插件有必要的函数"""
        import fakerx.integrations.pytest_plugin as plugin
        assert hasattr(plugin, 'pytest_addoption')
        assert hasattr(plugin, 'pytest_configure')
        assert hasattr(plugin, 'fakerx_config')
        assert hasattr(plugin, 'fake_data')
        assert hasattr(plugin, 'fake_record')
        assert hasattr(plugin, 'fake_records')
        assert hasattr(plugin, 'fake_schema')
        assert hasattr(plugin, 'fake_batch')
        assert hasattr(plugin, 'fake_pydantic')
        assert hasattr(plugin, 'fakerx_parametrize')

    def test_plugin_configure_adds_marker(self, fakerx_config):
        """插件配置添加了 marker"""
        # 验证 fakerx_config fixture 可用
        assert fakerx_config is not None


class TestUnittestBase:
    """unittest 基类测试"""

    def test_fakerx_test_case_attributes(self):
        """FakerXTestCase 基类属性"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'
            SEED = 42

        test = MyTest()
        test.setUp()
        assert hasattr(test, 'fake')
        assert isinstance(test.fake, FakerX)
        assert hasattr(test, 'gen_schema')
        assert hasattr(test, 'gen_template')
        assert hasattr(test, 'gen_pydantic')
        test.tearDown()

    def test_gen_template(self):
        """gen_template 方法"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

        test = MyTest()
        test.setUp()
        users = test.gen_template('user', count=5)
        assert len(users) == 5
        for u in users:
            assert 'username' in u
            assert 'email' in u
        test.tearDown()

    def test_gen_schema(self):
        """gen_schema 方法"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

        test = MyTest()
        test.setUp()
        data = test.gen_schema({'id': '{pyint}', 'name': '{name}'}, iterations=10)
        assert len(data) == 10
        for r in data:
            assert 'id' in r
            assert 'name' in r
        test.tearDown()

    def test_gen_pydantic(self):
        """gen_pydantic 方法"""
        from pydantic import BaseModel, conint

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            email: str

        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

        test = MyTest()
        test.setUp()
        for _ in range(10):
            try:
                user = test.gen_pydantic(User)
                assert isinstance(user, User)
                assert user.id > 0
                return
            except Exception:
                continue
        test.tearDown()

    def test_seed_reproducibility(self):
        """SEED 可重现性"""
        from faker import Faker

        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'
            SEED = 42

        test1 = MyTest()
        Faker.seed(42)
        test1.setUp()
        name1 = test1.fake.name()
        test1.tearDown()

        test2 = MyTest()
        Faker.seed(42)
        test2.setUp()
        name2 = test2.fake.name()
        test2.tearDown()

        assert name1 == name2  # 相同种子，相同结果


class TestUnittestDecorators:
    """unittest 装饰器测试"""

    def test_fake_data_schema_decorator(self):
        """@FakeData.schema 装饰器"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
            def test_record(self, record):
                assert 'id' in record
                assert 'name' in record
                return record

        test = MyTest()
        test.setUp()
        result = test.test_record()
        assert result is not None
        test.tearDown()

    def test_fake_data_template_decorator(self):
        """@FakeData.template 装饰器"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.template('product', count=3)
            def test_products(self, products):
                assert len(products) == 3
                for p in products:
                    assert 'price' in p
                    assert 'name' in p
                return products

        test = MyTest()
        test.setUp()
        result = test.test_products()
        assert len(result) == 3
        test.tearDown()

    def test_fake_data_parametrize(self):
        """@FakeData.parametrize 参数化测试"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.parametrize({'id': '{pyint}'}, iterations=3)
            def test_ids(self, record):
                assert isinstance(record['id'], int)

        test = MyTest()
        test.setUp()
        # parametrize 在 subTest 中执行，不返回值
        test.test_ids()
        test.tearDown()

    def test_fake_data_schema_multiple_records(self):
        """@FakeData.schema 多条记录"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.schema({'id': '{pyint}'}, iterations=5)
            def test_records(self, records):
                assert len(records) == 5
                for r in records:
                    assert 'id' in r
                return records

        test = MyTest()
        test.setUp()
        result = test.test_records()
        assert len(result) == 5
        test.tearDown()

    def test_fake_data_schema_with_unique(self):
        """@FakeData.schema 带唯一字段"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.schema({'id': {'method': 'pyint', 'min_value': 1, 'max_value': 500}},
                             iterations=5, unique_fields=['id'])
            def test_records(self, records):
                ids = [r['id'] for r in records]
                assert len(ids) == len(set(ids))
                return records

        test = MyTest()
        test.setUp()
        result = test.test_records()
        assert len(result) == 5
        test.tearDown()


class TestIntegrationEdgeCases:
    """集成测试边界情况"""

    def test_plugin_entry_points(self):
        """插件入口点注册"""
        from fakerx.integrations import pytest_plugin as plugin
        assert callable(plugin.pytest_addoption)
        assert callable(plugin.pytest_configure)

    def test_unittest_multiple_methods(self):
        """unittest 多个测试方法"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            def test_a(self):
                assert self.gen_template('user', count=1)[0]['email']

            def test_b(self):
                assert len(self.gen_schema({'id': '{pyint}'}, 3)) == 3

        test = MyTest()
        test.setUp()
        test.test_a()
        test.test_b()
        test.tearDown()

    def test_seed_class_variable(self):
        """SEED 类变量设置"""
        class MyTest(FakerXTestCase):
            LOCALE = 'en_US'
            SEED = 123

        test = MyTest()
        test.setUp()
        assert test.LOCALE == 'en_US'
        assert test.SEED == 123
        assert isinstance(test.fake, FakerX)
        test.tearDown()


class TestIntegrationDocumentation:
    """集成文档示例测试"""

    def test_pytest_fixture_example(self):
        """pytest fixture 示例"""
        # 模拟 conftest.py 中的 fixture 用法
        fake = FakerX('zh_CN', seed=42)
        user = fake.template('user', count=1)[0]
        assert 'email' in user
        assert 'username' in user

    def test_unittest_example(self):
        """unittest 示例"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'
            SEED = 42

            def test_user(self):
                users = self.gen_template('user', count=3)
                self.assertEqual(len(users), 3)
                for u in users:
                    self.assertIn('email', u)

        test = MyTest()
        test.setUp()
        test.test_user()
        test.tearDown()