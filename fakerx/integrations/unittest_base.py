# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:12
# @Software  : PyCharm
# @FileName  : unittest_base.py
# -----------------------------
"""
unittest 基类 - 提供 FakerX 数据生成能力

使用方式:
    from fakerx.integrations.unittest_base import FakerXTestCase

    class MyTest(FakerXTestCase):
        def test_user(self):
            user = self.fake.template('user', count=1)[0]
            self.assertIn('email', user)

        @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
        def test_with_schema(self, record):
            self.assertIn('id', record)
"""

import unittest
from functools import wraps
from typing import Dict, List, Optional


class FakerXTestCase(unittest.TestCase):
    """
    unittest 基类，自动提供 FakerX 实例

    属性:
        self.fake: FakerX 实例 (每个测试方法自动重置)

    方法:
        self.gen_schema(schema, iterations=1) -> List[Dict]
        self.gen_template(name, count=1) -> List[Dict]
        self.gen_pydantic(model_class) -> model instance
    """

    LOCALE = 'zh_CN'
    SEED = None  # 设置整数可固定随机种子

    @classmethod
    def setUpClass(cls):
        from fakerx import FakerX
        from faker import Faker
        if cls.SEED is not None:
            Faker.seed(cls.SEED)

    def setUp(self):
        from fakerx import FakerX
        self.fake = FakerX(self.LOCALE)

    def gen_schema(self, schema: Dict, iterations: int = 1, **kwargs) -> List[Dict]:
        """生成 Schema 数据"""
        return self.fake.schema(schema, iterations=iterations, **kwargs)

    def gen_template(self, name: str, count: int = 1, **kwargs) -> List[Dict]:
        """使用模板生成数据"""
        return self.fake.template(name, count=count, **kwargs)

    def gen_pydantic(self, model_class, **overrides):
        """生成 Pydantic 模型数据"""
        from fakerx.validators import generate_pydantic_model
        return generate_pydantic_model(self.fake, model_class, **overrides)


class FakeData:
    """unittest 装饰器工具类"""

    @staticmethod
    def schema(schema: Dict, iterations: int = 1, **schema_kwargs):
        """
        装饰器: 注入 Schema 生成的数据

        Example:
            class MyTest(FakerXTestCase):
                @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
                def test_user(self, record):
                    self.assertIn('id', record)
        """

        def decorator(func):
            def wrapper(self, *args, **kwargs):
                from fakerx import FakerX
                fake = FakerX(self.LOCALE)
                data = fake.schema(schema, iterations=iterations, **schema_kwargs)

                if iterations == 1:
                    kwargs['record'] = data[0]
                else:
                    kwargs['records'] = data

                return func(self, *args, **kwargs)

            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__
            return wrapper

        return decorator

    @staticmethod
    def template(name: str, count: int = 1, **template_kwargs):
        """
        装饰器: 注入模板生成的数据

        Example:
            class MyTest(FakerXTestCase):
                @FakeData.template('user', count=5)
                def test_users(self, users):
                    self.assertEqual(len(users), 5)
        """

        def decorator(func):
            def wrapper(self, *args, **kwargs):
                from fakerx import FakerX
                fake = FakerX(self.LOCALE)
                data = fake.template(name, count=count, **template_kwargs)
                kwargs[name + 's'] = data
                return func(self, *args, **kwargs)

            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__
            return wrapper

        return decorator

    @staticmethod
    def parametrize(schema: Dict, iterations: int = 10):
        """
        参数化测试: 为每条数据创建一个子测试

        Example:
            class MyTest(FakerXTestCase):
                @FakeData.parametrize({'id': '{pyint}'}, iterations=5)
                def test_ids(self, record):
                    self.assertIsInstance(record['id'], int)
        """

        def decorator(func):
            def wrapper(self, *args, **kwargs):
                from fakerx import FakerX
                fake = FakerX(self.LOCALE)
                data = fake.schema(schema, iterations=iterations)

                for i, record in enumerate(data):
                    with self.subTest(record_index=i):
                        func(self, record=record, *args, **kwargs)

            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__
            return wrapper

        return decorator
