# -*- coding: utf-8 -*-
"""
unittest 集成测试 - 验证 FakerXTestCase 基类和 FakeData 装饰器
"""
import unittest
from fakerx import FakerX
from fakerx.integrations.unittest_base import FakerXTestCase, FakeData


class TestUserGeneration(FakerXTestCase):
    """用户数据生成测试"""
    LOCALE = 'zh_CN'
    SEED = 42

    def test_template(self):
        """模板生成"""
        users = self.gen_template('user', count=5)
        self.assertEqual(len(users), 5)
        for u in users:
            self.assertIn('username', u)
            self.assertIn('email', u)

    def test_schema(self):
        """Schema 生成"""
        data = self.gen_schema({'id': '{pyint}', 'name': '{name}'}, iterations=10)
        self.assertEqual(len(data), 10)
        for r in data:
            self.assertIn('id', r)
            self.assertIn('name', r)

    def test_pydantic(self):
        """Pydantic 模型生成"""
        from pydantic import BaseModel, conint

        class User(BaseModel):
            id: conint(gt=0)
            name: str
            email: str

        for _ in range(10):
            try:
                user = self.gen_pydantic(User)
                self.assertIsInstance(user, User)
                self.assertGreater(user.id, 0)
                return
            except Exception:
                continue
        self.fail("无法生成有效的 Pydantic 模型")

    @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
    def test_with_decorator(self, record):
        """@FakeData.schema 装饰器"""
        self.assertIn('id', record)
        self.assertIn('name', record)

    @FakeData.schema({'id': '{pyint}'}, iterations=5)
    def test_with_decorator_multiple(self, records):
        """@FakeData.schema 多条记录"""
        self.assertEqual(len(records), 5)
        for r in records:
            self.assertIn('id', r)

    @FakeData.template('product', count=3)
    def test_products(self, products):
        """@FakeData.template 装饰器"""
        self.assertEqual(len(products), 3)
        for p in products:
            self.assertIn('price', p)
            self.assertIn('name', p)

    @FakeData.template('user', count=5, extend={'extra': '{pyint}'})
    def test_template_with_extend(self, users):
        """@FakeData.template 带扩展"""
        self.assertEqual(len(users), 5)
        for u in users:
            self.assertIn('extra', u)

    @FakeData.parametrize({'id': '{pyint}'}, iterations=5)
    def test_parametrized(self, record):
        """@FakeData.parametrize 参数化"""
        self.assertIsInstance(record['id'], int)

    @FakeData.schema({'id': {'method': 'pyint', 'min_value': 1, 'max_value': 500}},
                     iterations=5, unique_fields=['id'])
    def test_unique_fields(self, records):
        """唯一字段约束"""
        ids = [r['id'] for r in records]
        self.assertEqual(len(ids), len(set(ids)))


class TestFakerXTestCaseBase(unittest.TestCase):
    """FakerXTestCase 基类功能测试"""

    def test_setup_creates_fake(self):
        """setUp 创建 FakerX 实例"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

        test = MyTest()
        test.setUp()
        self.assertIsInstance(test.fake, FakerX)
        self.assertTrue(hasattr(test, 'gen_schema'))
        self.assertTrue(hasattr(test, 'gen_template'))
        self.assertTrue(hasattr(test, 'gen_pydantic'))
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

        self.assertEqual(name1, name2)

    def test_locale_setting(self):
        """LOCALE 设置"""
        class MyTest(FakerXTestCase):
            LOCALE = 'en_US'

        test = MyTest()
        test.setUp()
        name = test.fake.name()
        # 英文名应该包含字母
        self.assertTrue(any(c.isalpha() for c in name))
        test.tearDown()

    def test_multiple_test_methods(self):
        """多个测试方法"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            def test_a(self):
                users = self.gen_template('user', count=2)
                self.assertEqual(len(users), 2)

            def test_b(self):
                data = self.gen_schema({'id': '{pyint}'}, 3)
                self.assertEqual(len(data), 3)

        test = MyTest()
        test.setUp()
        test.test_a()
        test.test_b()
        test.tearDown()


class TestFakeDataDecorators(unittest.TestCase):
    """FakeData 装饰器功能测试"""

    def test_schema_decorator(self):
        """@FakeData.schema"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
            def test_record(self, record):
                self.assertIn('id', record)
                self.assertIn('name', record)
                return record

        test = MyTest()
        test.setUp()
        result = test.test_record()
        self.assertIsNotNone(result)
        test.tearDown()

    def test_template_decorator(self):
        """@FakeData.template"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.template('product', count=3)
            def test_products(self, products):
                self.assertEqual(len(products), 3)
                return products

        test = MyTest()
        test.setUp()
        result = test.test_products()
        self.assertEqual(len(result), 3)
        test.tearDown()

    def test_parametrize_decorator(self):
        """@FakeData.parametrize"""
        class MyTest(FakerXTestCase):
            LOCALE = 'zh_CN'

            @FakeData.parametrize({'id': '{pyint}'}, iterations=3)
            def test_ids(self, record):
                self.assertIsInstance(record['id'], int)

        test = MyTest()
        test.setUp()
        test.test_ids()
        test.tearDown()


if __name__ == '__main__':
    unittest.main()