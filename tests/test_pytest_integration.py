# -*- coding: utf-8 -*-
"""
pytest 集成测试 - 验证 fixture 和装饰器在真实 pytest 环境中的工作
"""
import pytest
from fakerx.integrations.pytest_plugin import (
    fake_schema, fake_batch, fake_pydantic, fakerx_parametrize,
)


# ========== fixture 方式 ==========

def test_fake_data_fixture(fake_data):
    """fake_data fixture 提供 FakerX 实例"""
    user = fake_data.template('user', count=1)[0]
    assert 'email' in user
    assert 'username' in user
    assert 'phone' in user

def test_fake_data_creates_schema(fake_data):
    """fake_data 创建 Schema 数据"""
    data = fake_data.schema({'id': '{pyint}', 'name': '{name}'}, iterations=5)
    assert len(data) == 5
    for r in data:
        assert 'id' in r
        assert 'name' in r

def test_fake_record_fixture(fake_record):
    """fake_record fixture 生成单条记录"""
    record = fake_record({'id': '{pyint}', 'name': '{name}'})
    assert 'id' in record
    assert 'name' in record

def test_fake_records_fixture(fake_records):
    """fake_records fixture 生成多条记录"""
    users = fake_records({'id': '{pyint}', 'name': '{name}'}, iterations=10)
    assert len(users) == 10
    for u in users:
        assert 'id' in u
        assert 'name' in u


# ========== 装饰器方式 ==========

@fake_schema({'id': '{pyint}', 'name': '{name}'})
def test_single_record(record):
    """@fake_schema 单条记录"""
    assert 'id' in record
    assert 'name' in record

@fake_schema({'id': '{pyint}'}, iterations=5)
def test_multiple_records(records):
    """@fake_schema 多条记录"""
    assert len(records) == 5

@fake_schema({'id': {'method': 'pyint', 'min_value': 1, 'max_value': 1000}},
             iterations=10, unique_fields=['id'])
def test_unique_records(records):
    """@fake_schema 带唯一字段"""
    assert len(records) == 10
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids))

@fake_batch('user', count=3)
def test_template_batch(users):
    """@fake_batch 模板批量生成"""
    assert len(users) == 3
    for u in users:
        assert 'username' in u
        assert 'email' in u

@fake_batch('product', count=2, extend={'extra': '{pyint}'})
def test_template_batch_with_extend(products):
    """@fake_batch 带扩展"""
    assert len(products) == 2
    for p in products:
        assert 'price' in p
        assert 'extra' in p

# ========== Pydantic ==========

# @fake_pydantic 需要直接传入模型类，在测试函数中手动测试
def test_pydantic_single(fake_data):
    """@fake_pydantic 功能"""
    from pydantic import BaseModel, conint

    class User(BaseModel):
        id: conint(gt=0)
        name: str
        email: str

    user = fake_data.pydantic(User)
    assert isinstance(user, User)
    assert user.id > 0
    assert isinstance(user.name, str)

# ========== 参数化测试 ==========

@fakerx_parametrize({'id': '{pyint}', 'name': '{name}'}, iterations=5)
def test_each_record(record):
    """@fakerx_parametrize 参数化"""
    assert isinstance(record['id'], int)
    assert isinstance(record['name'], str)


# ========== 复杂场景 ==========

@fake_schema({
    'user': {'name': '{name}', 'email': '{email}'},
    'meta': {'level': {'elements': ['A', 'B', 'C']}}
})
def test_nested_schema(record):
    """嵌套 Schema"""
    assert 'user' in record
    assert 'meta' in record
    assert 'name' in record['user']
    assert record['meta']['level'] in ['A', 'B', 'C']

@fake_schema({'id': '{pyint}', 'name': '{name}'}, iterations=500)
def test_large_dataset(records):
    """大数据集"""
    assert len(records) == 500