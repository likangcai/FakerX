# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:12
# @Software  : PyCharm
# @FileName  : pytest_plugin.py
# -----------------------------
"""
pytest 插件 - 提供 fixture 和装饰器

安装方式:
    # pyproject.toml
    [project.entry-points.pytest11]
    fakerx = "fakerx.integrations.pytest_plugin"

使用方式:
    # conftest.py 中无需额外配置，安装后自动生效

    # test_example.py
    def test_user(fake_data):
        user = fake_data.template('user', count=1)[0]
        assert 'email' in user

    @fake_schema({'id': '{pyint}', 'name': '{name}'})
    def test_with_schema(record):
        assert 'id' in record
        assert 'name' in record

    @fake_batch('user', count=5)
    def test_batch(users):
        assert len(users) == 5
"""

import pytest
from functools import wraps
from typing import Dict, List, Optional, Callable


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        '--fakerx-locale',
        action='store',
        default='zh_CN',
        help='FakerX locale (default: zh_CN)',
    )
    parser.addoption(
        '--fakerx-seed',
        action='store',
        type=int,
        default=None,
        help='FakerX random seed for reproducible data',
    )


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        'markers',
        'fakerx_schema(schema): specify schema for fake_schema fixture'
    )


@pytest.fixture(scope='session')
def fakerx_config(request):
    """会话级 FakerX 配置"""
    locale = request.config.getoption('--fakerx-locale')
    seed = request.config.getoption('--fakerx-seed')
    return {'locale': locale, 'seed': seed}


@pytest.fixture(scope='session')
def fake_data(fakerx_config):
    """
    会话级 FakerX 实例

    在测试中直接使用:
        def test_something(fake_data):
            user = fake_data.template('user', count=1)[0]
    """
    from fakerx import FakerX
    fake = FakerX(fakerx_config['locale'])

    if fakerx_config['seed'] is not None:
        from faker import Faker as _F
        _F.seed(fakerx_config['seed'])

    return fake


@pytest.fixture
def fake_record(fake_data):
    """
    生成单条记录的 fixture

    使用 marker 指定 schema:
        @pytest.mark.fakerx_schema({'id': '{pyint}', 'name': '{name}'})
        def test_record(fake_record):
            assert 'id' in fake_record
    """

    def _generate(schema: Dict, **kwargs):
        return fake_data.schema(schema, iterations=1, **kwargs)[0]

    return _generate


@pytest.fixture
def fake_records(fake_data):
    """
    生成多条记录的 fixture

    使用:
        def test_users(fake_records):
            users = fake_records(
                {'id': '{pyint}', 'name': '{name}'},
                iterations=10
            )
            assert len(users) == 10
    """

    def _generate(schema: Dict, iterations: int = 10, **kwargs):
        return fake_data.schema(schema, iterations=iterations, **kwargs)

    return _generate


# ----------------------------------------------------------------
# 装饰器形式的 fixture
# ----------------------------------------------------------------

def fake_schema(schema: Dict, iterations: int = 1, **schema_kwargs):
    """
    装饰器: 为测试函数注入生成的数据

    Example:
        @fake_schema({'id': '{pyint}', 'name': '{name}'})
        def test_user(record):
            assert 'id' in record
            assert 'name' in record

        @fake_schema({'id': '{pyint}'}, iterations=5)
        def test_users(records):
            assert len(records) == 5
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            from fakerx import FakerX
            fake = FakerX()
            data = fake.schema(schema, iterations=iterations, **schema_kwargs)

            if iterations == 1:
                kwargs['record'] = data[0]
            else:
                kwargs['records'] = data

            return func(*args, **kwargs)

        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def fake_batch(template_name: str, count: int = 10, **template_kwargs):
    """
    装饰器: 使用模板批量生成数据并注入测试

    Example:
        @fake_batch('user', count=5)
        def test_users(users):
            assert len(users) == 5
            for u in users:
                assert 'email' in u
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            from fakerx import FakerX
            fake = FakerX()
            data = fake.template(template_name, count=count, **template_kwargs)
            kwargs[template_name + 's'] = data
            return func(*args, **kwargs)

        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def fake_pydantic(model_class, count: int = 1, **overrides):
    """
    装饰器: 生成 Pydantic 模型数据并注入测试

    Example:
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str

        @fake_pydantic(User, count=3)
        def test_users(users):
            for u in users:
                assert isinstance(u, User)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from fakerx import FakerX
            from fakerx.validators import generate_pydantic_model
            fake = FakerX()

            if count == 1:
                kwargs['model'] = generate_pydantic_model(fake, model_class, **overrides)
            else:
                kwargs['models'] = [
                    generate_pydantic_model(fake, model_class, **overrides)
                    for _ in range(count)
                ]
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ----------------------------------------------------------------
# 参数化测试数据
# ----------------------------------------------------------------

def fakerx_parametrize(schema: Dict, iterations: int = 10, ids=None):
    """
    参数化测试: 每条数据作为一个测试用例

    Example:
        @fakerx_parametrize({'id': '{pyint}', 'name': '{name}'}, iterations=5)
        def test_user_id_positive(record):
            assert record['id'] > 0

        # 等价于 5 个独立的测试用例
    """
    from fakerx import FakerX
    fake = FakerX()
    data = fake.schema(schema, iterations=iterations)

    def decorator(func):
        @pytest.mark.parametrize('record', data, ids=ids)
        @wraps(func)
        def wrapper(record, *args, **kwargs):
            return func(record, *args, **kwargs)

        return wrapper

    return decorator
