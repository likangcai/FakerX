# FakerX

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![Tests](https://img.shields.io/badge/Tests-351%20passing-brightgreen)]()

FakerX 是一个强大的 Python 测试数据生成库，基于 [Faker](https://github.com/joke2k/faker) 的增强版。**完全兼容原生 Faker**（`isinstance(fake, Faker) == True`），提供结构化数据生成、上下文感知、数据验证、多格式导出、国际化等企业级功能。

---

## 📦 安装

```bash
# 基础安装
pip install fakerx

# 完整安装（Excel、Parquet、Pydantic 支持）
pip install fakerx[all]

# 开发安装
pip install -e .[dev]
```

---

## 🚀 快速开始

### 基础用法（完全兼容 Faker）

```python
from fakerx import FakerX
from faker import Faker

fake = FakerX('zh_CN', seed=42)

# 所有 Faker 方法完全可用
name = fake.name()                    # 王丹
address = fake.address()              # 北京市...
phone = fake.phone_number()           # 13812345678
email = fake.email()                  # user@example.com

# isinstance 检查通过
assert isinstance(fake, Faker)        # True
```

### 结构化数据生成

```python
# 最简单的 Schema
data = fake.schema({
    'id': '{pyint}',
    'username': '{user_name}',
    'email': '{email}',
    'profile': {
        'level': {'elements': ['初级', '中级', '高级']}
    }
}, iterations=2)
# 输出: [{'id': 1234, 'username': 'zhang', 'email': '...', 'profile': {'level': '中级'}}, ...]
```

---

## 🎯 核心增强功能

### 1. 📐 上下文感知生成

#### 自增序列号

```python
# {seq:名称:起始值:步长}
data = fake.schema({
    'id': '{seq:user_id:1:1}',        # 1, 2, 3, 4, 5...
    'order_no': '{seq:order:1000:1}',  # 1000, 1001, 1002...
    'name': '{name}',
}, iterations=5)
# data[0]['id'] == 1, data[1]['id'] == 2, ...
```

#### 条件逻辑

```python
data = fake.schema({
    'user_type': {'elements': ['vip', 'normal'], 'weights': [0.3, 0.7]},
    'discount': {
        'if': {'user_type': 'vip'},           # 条件
        'then': {'method': 'pyfloat', 'min_value': 0.5, 'max_value': 0.8},  # VIP 折扣
        'else': {'method': 'pyfloat', 'min_value': 0.9, 'max_value': 1.0},  # 普通折扣
    },
    'level_name': {
        'expr': '${user_type}_${discount}'    # 表达式拼接
    }
}, iterations=10)
```

#### 字段引用

```python
data = fake.schema({
    'user_type': {'elements': ['vip', 'normal']},
    'ref_type': {'ref': 'user_type'},          # 引用前一个字段的值
    'label': {'expr': 'User-${user_type}'},    # 表达式引用
}, iterations=5)
# ref_type 始终等于 user_type 的值
```

#### 跨表关联

```python
# 先生成用户表
users = fake.schema({
    'id': '{seq:uid:1:1}',
    'name': '{name}',
}, iterations=5)

# 生成订单表，关联用户表
orders = fake.schema({
    'order_id': '{seq:oid:1000:1}',
    'user_id': {'method': 'pyint'},                     # 从 users 的 id 中取值
    'amount': {'method': 'pyfloat', 'min_value': 10, 'max_value': 9999},
}, iterations=20, foreign_keys={'user_id': ([u['id'] for u in users], 'id')})
# 每个 order 的 user_id 都来自 users 表的 id 字段
```

#### 多表关联生成

```python
# 一键生成多表关联数据
config = {
    'users': {
        'schema': {'id': '{seq:uid:1:1}', 'name': '{name}'},
        'count': 5,
    },
    'orders': {
        'schema': {
            'order_id': '{seq:oid:1000:1}',
            'user_id': {'method': 'pyint'},
            'amount': {'method': 'pyfloat', 'min_value': 10, 'max_value': 9999},
        },
        'count': 20,
        'relations': {'user_id': 'users.id'}  # 引用 users 表的 id
    }
}
result = fake.generate_relations(config)
# result['users'] -> 5 条用户
# result['orders'] -> 20 条订单，每条关联到 users
```

### 2. 📋 预设模板系统

内置 5 种常用业务模板：

```python
# 用户模板
users = fake.template('user', count=3)
# [{'id': 123, 'username': 'zhang', 'email': '...', 'phone': '...', 'status': 'active'}, ...]

# 商品模板
products = fake.template('product', count=3)
# [{'id': 456, 'name': '...', 'price': 99.99, 'stock': 100, 'category': '电子', 'sku': 'ABC-1234'}, ...]

# 订单模板
orders = fake.template('order', count=3)
# [{'order_id': 'ORD-12345678', 'user_id': 789, 'total_amount': 299.00, 'status': 'paid', ...}, ...]

# 文章模板
articles = fake.template('article', count=3)
# [{'id': 111, 'title': '...', 'content': '...', 'author': '张三', 'tags': [...], 'views': 500}, ...]

# 日志模板
logs = fake.template('log', count=3)
# [{'timestamp': '2024-01-01 12:00:00', 'level': 'INFO', 'message': '...', 'service': 'api-gateway', ...}, ...]
```

#### 模板扩展与覆盖

```python
# 扩展模板（添加额外字段）
users = fake.template('user', count=5, extend={
    'department': {'elements': ['技术部', '市场部', '财务部']},
    'salary': {'method': 'pyint', 'min_value': 5000, 'max_value': 50000},
})

# 覆盖模板字段
users = fake.template('user', count=5, override={
    'status': {'elements': ['active']},  # 全部为 active
})

# 注册自定义模板
fake.register_template('employee', {
    'id': '{seq:emp_id:1000:1}',
    'name': '{name}',
    'department': {'elements': ['技术', '市场', '财务']},
    'salary': {'method': 'pyint', 'min_value': 8000, 'max_value': 80000},
}, description='员工模型')

# 列出所有模板
templates = fake.list_templates()
# {'user': '标准用户模型', 'product': '电商商品模型', 'employee': '员工模型', ...}
```

### 3. ✅ 数据验证系统

#### Schema 内置验证规则

```python
from fakerx.validators import TypeRule, RangeRule, RegexRule, ChoiceRule, CrossFieldRule

schema = {
    'id': {
        'method': 'pyint',
        'min_value': 1,
        'max_value': 9999,
        'validate': [TypeRule(int), RangeRule(1, 9999)]  # 类型 + 范围检查
    },
    'email': {
        'method': 'email',
        'validate': [RegexRule(r'^[\w.]+@[\w.]+\.[\w.]+$')]  # 正则匹配
    },
    'status': {
        'elements': ['active', 'inactive', 'banned'],
        'validate': [ChoiceRule(['active', 'inactive', 'banned'])]  # 枚举检查
    },
    'start_date': {'method': 'date_this_year'},
    'end_date': {
        'method': 'date_this_year',
        'validate': [CrossFieldRule('start_date', 'gt')]  # 跨字段: end_date > start_date
    },
}

# 生成时自动验证，验证失败抛出 FakerXError
data = fake.schema(schema, iterations=10)
```

#### Schema 定义验证

```python
# 验证 Schema 定义本身的合法性
schema = {
    'id': {'method': 'pyint', 'min_value': 100, 'max_value': 50},  # min > max，错误！
}
is_valid = fake.validate_schema(schema, verbose=True)
# 输出: 错误:
#   - 字段 'id': min_value (100) 大于 max_value (50)
```

#### Pydantic 集成

```python
from pydantic import BaseModel, conint, EmailStr, Field

class User(BaseModel):
    id: conint(gt=0)
    name: str
    email: str
    age: conint(ge=18, le=65) = Field(default=30)

# 自动生成并验证 Pydantic 模型
user = fake.pydantic(User)
# user.id > 0, 18 <= user.age <= 65, user.email 是有效邮箱

# 覆盖特定字段
user = fake.pydantic(User, age=25, email='test@example.com')
```

### 4. 🎭 数据脱敏

```python
# 单字段脱敏
fake.anonymize('13812345678', 'phone')      # 138****5678
fake.anonymize('test@example.com', 'email')  # t***@example.com
fake.anonymize('110101199001011234', 'id_card')  # 110101********1234
fake.anonymize('张三', 'name')               # 张*
fake.anonymize('北京市朝阳区建国路88号', 'address')  # 北京市朝阳区****

# 自动识别类型
fake.anonymize('13812345678')               # 自动识别为 phone
fake.anonymize('test@example.com')           # 自动识别为 email

# 批量脱敏
data = {'name': '张三', 'phone': '13812345678', 'email': 'a@b.com'}
result = fake.anonymize_dict(data, {
    'phone': 'phone',
    'email': 'email',
    'name': 'name',
})
# {'name': '张*', 'phone': '138****5678', 'email': 'a*@b.com'}

# 列表批量脱敏
records = [{'phone': '13812345678'}, {'phone': '13912345678'}]
result = fake.anonymize_list(records, {'phone': 'phone'})
```

### 5. 📊 多格式导出

支持 8 种格式，自动识别文件扩展名：

```python
# 智能导出（自动识别格式）
fake.export(data, 'users.csv')              # CSV
fake.export(data, 'users.xlsx')             # Excel
fake.export(data, 'users.json')             # JSON
fake.export(data, 'users.sql', table_name='users')  # SQL INSERT
fake.export(data, 'users.html', title='用户列表')   # HTML 表格
fake.export(data, 'users.yaml')             # YAML
fake.export(data, 'users.xml')              # XML
fake.export(data, 'users.parquet')          # Parquet

# 指定格式导出
fake.export(data, 'output', format='csv')

# v0.2.0 兼容：返回字符串
json_str = fake.to_json(data)    # 返回 JSON 字符串
csv_str = fake.to_csv(data)      # 返回 CSV 字符串

# 保存到文件
fake.to_json(data, 'data.json')
fake.to_csv(data, 'data.csv')

# 写入 SQLite 数据库
fake.to_database(data, 'users', 'test.db')
```

### 6. ⚡ 高性能批处理

#### 多进程并行

```python
# 10 万条数据，8 进程并行
data = fake.schema_parallel(
    {'id': '{pyint}', 'name': '{name}'},
    total_count=100000,
    workers=8,
)

# 带唯一约束
data = fake.schema_parallel(
    {'id': {'method': 'pyint', 'min_value': 1, 'max_value': 99999}},
    total_count=1000,
    workers=4,
    unique_fields=['id'],
)
```

#### 流式生成（内存恒定）

```python
# 百万级数据，内存恒定
gen = fake.schema_stream(
    {'id': '{seq:big_id:1:1}', 'name': '{name}'},
    iterations=1000000,
)
fake.export_stream(gen, 'million.csv')

# 分块生成
for chunk in fake.schema_chunks(
    {'id': '{pyint}', 'name': '{name}'},
    iterations=10000,
    chunk_size=1000,
):
    process_chunk(chunk)  # 每次处理 1000 条
```

#### 生成缓存

```python
from fakerx.batch import GenerationCache

cache = GenerationCache()

# 第一次生成，存入缓存
data1 = cache.get_or_generate({'id': '{pyint}'}, 10)

# 第二次相同参数，直接返回缓存
data2 = cache.get_or_generate({'id': '{pyint}'}, 10)
assert data1 == data2  # 完全相同

# 缓存统计
stats = cache.stats()
# {'entries': 1, 'total_records': 10}

# 清空缓存
cache.clear()
```

#### 异步生成

```python
import asyncio

async def main():
    # 异步批量生成
    data = await fake.schema_async(
        {'id': '{pyint}', 'name': '{name}'},
        total_count=1000,
        batch_size=100,  # 每批 100 条
    )

    # 异步流式生成
    async for record in fake.schema_async_stream(
        {'id': '{pyint}', 'name': '{name}'},
        total_count=1000,
    ):
        print(record)  # 逐条处理数据（如写入数据库、导出等）

asyncio.run(main())
```

### 7. 🌍 国际化支持

支持 16 种 locale，运行时切换，多语言混合生成：

| 层级 | 数量 | 说明 |
|---|---|---|
| **`SUPPORTED_LOCALES`** | **16 种** | 所有 locale 均可正常生成 `name()`、`address()`、`phone_number()` 等数据 |
| **`LOCALE_CONFIG`** | **4 种**（zh_CN/en_US/ja_JP/fr_FR） | 额外提供手机格式、邮编格式、货币符号、日期格式等地区特有配置 |

其余 12 种 locale（zh_TW、en_GB、ko_KR、de_DE、es_ES 等）使用 Faker 库的默认配置，**所有数据生成功能正常**。

```python
# 列出所有支持的 locale
from fakerx.i18n import SUPPORTED_LOCALES
# {'zh_CN': '简体中文', 'en_US': 'English (US)', 'ja_JP': '日本語', ...}

# 切换 locale
fake.switch_locale('en_US')
name = fake.name()  # John Smith

fake.switch_locale('ja_JP')
name = fake.name()  # 山田 太郎

# 多语言混合生成
data = fake.generate_localized(
    {'name': '{name}', 'city': '{city}', 'address': '{address}'},
    iterations=100,
    locale_weights={
        'zh_CN': 0.6,   # 60% 中文
        'en_US': 0.3,   # 30% 英文
        'ja_JP': 0.1,   # 10% 日文
    },
)
# 每条记录包含 _locale 字段标识语言
```

### 8. 🧪 测试框架集成

#### pytest 插件（自动注册）

安装后自动生效，无需额外配置：

```python
# conftest.py 中无需配置，插件自动注册

# test_user.py

# 使用 fixture
def test_user_data(fake_data):
    """fake_data 提供 FakerX 实例"""
    user = fake_data.template('user', count=1)[0]
    assert 'email' in user
    assert 'username' in user

def test_batch_data(fake_records):
    """fake_records 生成多条记录"""
    users = fake_records({'id': '{pyint}', 'name': '{name}'}, iterations=10)
    assert len(users) == 10

def test_single_record(fake_record):
    """fake_record 生成单条记录"""
    record = fake_record({'id': '{pyint}', 'name': '{name}'})
    assert 'id' in record

# 使用装饰器
from fakerx.integrations.pytest_plugin import (
    fake_schema, fake_batch, fake_pydantic, fakerx_parametrize
)

@fake_schema({'id': '{pyint}', 'name': '{name}'})
def test_single(record):
    """@fake_schema 注入单条记录"""
    assert 'id' in record
    assert 'name' in record

@fake_schema({'id': '{pyint}'}, iterations=5, unique_fields=['id'])
def test_multiple(records):
    """@fake_schema 注入多条记录，带唯一约束"""
    assert len(records) == 5
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids))  # 全部唯一

@fake_batch('user', count=3, extend={'role': '{pyint}'})
def test_batch(users):
    """@fake_batch 使用模板生成"""
    assert len(users) == 3
    for u in users:
        assert 'username' in u
        assert 'role' in u

@fake_pydantic(User, count=1)
def test_pydantic(model):
    """@fake_pydantic 生成 Pydantic 模型"""
    assert isinstance(model, User)
    assert model.id > 0

@fakerx_parametrize({'id': '{pyint}'}, iterations=5)
def test_parametrize(record):
    """@fakerx_parametrize 参数化测试（每条数据一个测试用例）"""
    assert isinstance(record['id'], int)
```

#### pytest 命令行选项

```bash
# 运行测试时指定 locale 和种子
pytest --fakerx-locale en_US --fakerx-seed 42 tests/
```

#### unittest 基类

```python
from fakerx.integrations.unittest_base import FakerXTestCase, FakeData

class UserTest(FakerXTestCase):
    LOCALE = 'zh_CN'
    SEED = 42  # 固定种子，测试可重现

    def test_template(self):
        """gen_template 生成模板数据"""
        users = self.gen_template('user', count=5)
        self.assertEqual(len(users), 5)
        for u in users:
            self.assertIn('email', u)

    def test_schema(self):
        """gen_schema 生成 Schema 数据"""
        data = self.gen_schema({'id': '{pyint}', 'name': '{name}'}, iterations=10)
        self.assertEqual(len(data), 10)

    def test_pydantic(self):
        """gen_pydantic 生成 Pydantic 模型"""
        from pydantic import BaseModel, conint
        class User(BaseModel):
            id: conint(gt=0)
            name: str
        user = self.gen_pydantic(User)
        self.assertIsInstance(user, User)
        self.assertGreater(user.id, 0)

    @FakeData.schema({'id': '{pyint}', 'name': '{name}'})
    def test_with_decorator(self, record):
        """@FakeData.schema 装饰器注入"""
        self.assertIn('id', record)
        self.assertIn('name', record)

    @FakeData.schema({'id': '{pyint}'}, iterations=5, unique_fields=['id'])
    def test_unique_decorator(self, records):
        """@FakeData.schema 带唯一约束"""
        self.assertEqual(len(records), 5)
        ids = [r['id'] for r in records]
        self.assertEqual(len(ids), len(set(ids)))

    @FakeData.template('product', count=3)
    def test_template_decorator(self, products):
        """@FakeData.template 装饰器注入"""
        self.assertEqual(len(products), 3)
        for p in products:
            self.assertIn('price', p)

    @FakeData.parametrize({'id': '{pyint}'}, iterations=5)
    def test_parametrized(self, record):
        """@FakeData.parametrize 参数化"""
        self.assertIsInstance(record['id'], int)
```

### 9. 🔧 自定义 Provider

```python
# 方式1: 注册单个函数
@fake.register_provider('phone_cn')
def gen_phone(faker, **kw):
    prefixes = ['138', '139', '150', '188']
    prefix = faker.random_element(prefixes)
    return prefix + ''.join(str(faker.random_digit()) for _ in range(8))

data = fake.schema({'phone': '{phone_cn}'}, iterations=5)
# 每个 phone 都是 11 位手机号

# 方式2: 注册完整的 Provider 类
from faker.providers import BaseProvider

class MyProvider(BaseProvider):
    def custom_id(self):
        return f"CUST-{self.generator.pyint(min_value=1, max_value=9999)}"

    def status_code(self):
        return self.generator.random_element(['active', 'inactive', 'pending'])

fake.add_provider(MyProvider)

data = fake.schema({
    'id': '{custom_id}',
    'status': '{status_code}',
}, iterations=5)
```

### 10. 📝 数据后处理

```python
# 内置处理器
data = fake.schema({
    'name': '{name}',
    'email': '{email}',
    'price': {'method': 'pyfloat', 'min_value': 0, 'max_value': 100},
}, iterations=5, post_process={
    'name': ['strip', 'title'],       # 去空格 + 首字母大写
    'email': ['lower'],                # 转小写
    'price': ['round2'],               # 保留2位小数
    'desc': ['md5'],                   # MD5 哈希
})

# 可用的内置处理器
# upper, lower, strip, title, md5, sha256, base64
# round2, round4, to_int, to_str, to_float, none_if_empty

# 注册自定义处理器
fake.register_processor('double', lambda v: v * 2 if v else v)

# 数据去重
from fakerx.processors import PostProcessor
pp = PostProcessor()
records = [{'id': 1}, {'id': 2}, {'id': 1}]
result = pp.deduplicate(records, ['id'], keep='first')  # 保留第一条
result = pp.deduplicate(records, ['id'], keep='last')   # 保留最后一条
```

### 11. 📄 配置文件生成

```yaml
# config.yaml
schema:
  id: '{pyint}'
  name: '{name}'
  email: '{email}'
  age: {'method': 'pyint', 'min_value': 18, 'max_value': 65}
iterations: 100
unique_fields: ['email']
export:
  filepath: 'output/users.csv'
  format: 'csv'
```

```python
# 从配置文件生成
data = fake.generate_from_config('config.yaml')
# 自动生成数据并导出到 output/users.csv
```

---

## 🆕 FakerX 0.2.0 兼容方法

以下方法兼容旧版 v0.2.0 API，确保迁移平滑：

```python
fake.uuid4()                    # 生成 UUID 字符串
fake.custom_url('example.com')  # 自定义域名 URL
fake.validate_email('test@example.com')  # 邮箱格式验证
fake.set_seed(42)               # 设置随机种子（与 seed() 等价）
fake.stats(data)                # 数据统计信息
fake.batch('name', 10)          # 生成器方式批量生成
fake.clean_address()            # 地址去邮编
fake.random_date_between('2020-01-01', '2020-12-31')  # 日期范围
fake.generate_with_validation('email', lambda x: 'test' not in x)  # 带验证生成
fake.nested_schema(schema, 5)   # 等价于 schema()
fake.load_schema_from_file('schema.json')  # 加载 Schema 文件
```

---

## 💻 命令行工具

```bash
# 安装后使用
fakerx --help

# 基础用法
fakerx --method user_name --count 10                  # 生成10个用户名
fakerx --template user --count 100 --output users.csv  # 模板生成并导出

# 数据生成
fakerx --method name --count 1                        # 生成1个名字
fakerx --method email --count 5 --format json          # 5个邮箱，JSON格式
fakerx --method pyint --count 3 --seed 42              # 固定种子可重现

# Schema 和模板
fakerx --schema schema.json --count 50                 # 从 Schema 文件生成
fakerx --schema schema.json --count 1000 --workers 4   # 多进程并行生成
fakerx --template user --count 5 --unique username     # 唯一用户名
fakerx --template order --count 20 --stream            # 流式生成大订单数据

# 高级功能
fakerx --list-templates                     # 列出所有模板
fakerx --list-locales                       # 列出所有 locale
fakerx --validate schema.json               # 验证 Schema
fakerx --anonymize 13812345678 phone        # 数据脱敏
fakerx --generate-from-config config.yaml   # 从配置文件生成

# 输出格式
fakerx --template user --count 5 --format excel --output users.xlsx
fakerx --template user --count 5 --format csv --output users.csv
fakerx --template user --count 5 --format json --output users.json
fakerx --template user --count 5 --format sql --output users.sql
fakerx --template user --count 5 --format html --output users.html
fakerx --template user --count 5 --format yaml --output users.yaml
fakerx --template user --count 5 --format xml --output users.xml
fakerx --template user --count 5 --format parquet --output users.parquet

# 交互模式
fakerx --interactive
```

---

## 🏗️ 真实场景示例

### 电商测试数据

```python
# 生成完整电商测试数据
from fakerx import FakerX

fake = FakerX('zh_CN', seed=42)

# 1. 用户表
users = fake.template('user', count=100, extend={
    'vip_level': {'elements': ['普通', '黄金', '钻石'], 'weights': [0.6, 0.3, 0.1]},
    'register_date': '{date_time_this_year}',
})

# 2. 商品表
products = fake.template('product', count=50, override={
    'category': {'elements': ['手机', '电脑', '配件', '家居']},
})

# 3. 订单表（关联用户）
orders = fake.schema({
    'order_id': '{seq:order:10000:1}',
    'user_id': {'method': 'pyint'},
    'product_id': {'method': 'pyint'},
    'amount': {'method': 'pyfloat', 'min_value': 10, 'max_value': 9999},
    'quantity': {'method': 'pyint', 'min_value': 1, 'max_value': 10},
    'status': {'elements': ['pending', 'paid', 'shipped', 'delivered', 'cancelled']},
    'created_at': '{date_time_this_year}',
}, iterations=500, foreign_keys={
    'user_id': ([u['id'] for u in users], 'id'),
    'product_id': ([p['id'] for p in products], 'id'),
})

# 4. 导出为 Excel
fake.export(orders, 'orders.xlsx', title='订单数据')
```

### 日志数据生成

```python
# 生成系统日志数据
logs = fake.template('log', count=1000, extend={
    'ip': '{ipv4}',
    'user_agent': '{user_agent}',
    'duration_ms': {'method': 'pyint', 'min_value': 1, 'max_value': 5000},
})

# 导出为 CSV
fake.export(logs, 'system_logs.csv')
```

---

## 📁 项目结构

```
fakerx/
├── __init__.py          # 包入口，导出所有公开 API
├── __main__.py          # CLI 入口点
├── fakerx.py            # 主类 FakerX（继承 Faker）
├── schema.py            # Schema 生成器
├── context.py           # 上下文感知引擎
├── validators.py        # 数据验证系统
├── batch.py             # 高性能批处理
├── anonymizer.py        # 数据脱敏
├── processors.py        # 后处理器
├── templates.py         # 预设模板
├── i18n.py              # 国际化
├── cli.py               # 增强命令行
├── exceptions.py        # 自定义异常
├── exporters/           # 8 格式导出器
│   ├── __init__.py
│   ├── base.py
│   ├── csv_ex.py
│   ├── json_ex.py
│   ├── excel_ex.py
│   ├── sql_ex.py
│   ├── yaml_ex.py
│   ├── html_ex.py
│   ├── xml_ex.py
│   └── parquet_ex.py
├── integrations/        # 测试框架集成
│   ├── __init__.py
│   ├── pytest_plugin.py
│   └── unittest_base.py
└── providers/           # Provider 注册中心
    ├── __init__.py
    └── registry.py
```

---

## 📊 测试

```bash
# 运行全部测试
pytest tests/

# 运行特定模块测试
pytest tests/test_batch.py -v
pytest tests/test_integrations.py -v
pytest tests/test_validators.py -v

# 运行集成测试
pytest tests/test_pytest_integration.py -v
pytest tests/test_unittest_integration.py -v
```

---

## 🌐 跨平台支持

| 平台 | 状态 |
|---|---|
| **Windows** | ✅ 全部 351 个测试通过 |
| **macOS** | ✅ 全部测试通过 |
| **Linux** | ✅ 全部测试通过 |

---

## 📄 许可证

MIT

## 📬 联系我们

邮箱：yingzilkq@163.com <br>
如果您有任何问题或建议，请通过 [GitHub Issues](https://github.com/likangcai/FakerX/issues) 联系我们。