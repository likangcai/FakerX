from fakerx import FakerX

# 测试基础功能
fake = FakerX('zh_CN')

name = fake.name()
address = fake.address()
clean_address = fake.clean_address()
date = fake.date_of_birth()

print(f'生成姓名: {name}')
print(f'生成地址: {address}')
print(f'生成地址1: {clean_address}')
print(f'生成出生日期: {date}')

# 测试schema
user_schema = {
    'id': '{pyint}',
    'username': '{user_name}',
    'email': '{email}',
    'profile': {
        'level': {'elements': ['初级', '中级', '高级']}
    }
}

user_data = fake.schema(user_schema, iterations=2)
print(f'第一条用户数据: {user_data[0]}')
print(f'第二条用户数据: {user_data[1]}')

# 测试pydantic
from pydantic import BaseModel, EmailStr, conint

class User(BaseModel):
    id: conint(gt=0)
    name: str
    email: EmailStr

valid_user = fake.pydantic(User)
print(f'验证用户: {valid_user}')
print(f'已验证的用户数据: {valid_user}')
print(f'邮箱格式是否正确: {valid_user.email}')

# 测试batch（现在返回生成器）
usernames_gen = fake.batch('user_name', iterations=10, unique=True)
usernames_list = list(usernames_gen)
print(f'用户名: {usernames_list}')
# 使用生成器表达式，节省内存
first_five = usernames_list[:5]
print(f'批量生成的前5个唯一用户名: {first_five}')
print(f'用户名总数: {len(usernames_list)}')

# 测试新功能：random_date_between
random_date = fake.random_date_between('2020-01-01', '2023-12-31')
print(f'随机日期: {random_date}')

# 测试唯一字段
user_schema_unique = {
    'id': '{pyint}',
    'username': '{user_name}',
    'email': '{email}'
}

user_data_unique = fake.schema(user_schema_unique, iterations=3, unique_fields=['username', 'email'])
print(f'唯一用户数据: {user_data_unique}')

# 测试导出
json_output = fake.to_json(user_data_unique)
print(f'JSON输出: {json_output}')

csv_output = fake.to_csv(user_data_unique)
print(f'CSV输出: {csv_output}')

# 测试新功能：UUID
uid = fake.uuid4()
print(f'UUID: {uid}')

# 测试自定义URL
custom_url = fake.custom_url('example.com')
print(f'自定义URL: {custom_url}')

# 测试邮箱验证
is_valid = fake.validate_email('test@example.com')
is_invalid = fake.validate_email('invalid-email')
print(f'邮箱有效: {is_valid}, 无效: {is_invalid}')

# 测试随机种子
fake.set_seed(42)
name1 = fake.name()
fake.set_seed(42)
name2 = fake.name()
print(f'重现结果: {name1 == name2}, 姓名: {name1}')

# 测试批量生成器
usernames_gen = fake.batch('user_name', iterations=10, unique=True)
first_5_gen = list(usernames_gen)[:5]
print(f'生成器前5个用户名: {first_5_gen}')

# 测试数据统计
stats = fake.stats(user_data_unique)
print(f'数据统计: {stats}')

# 测试带验证的数据生成
valid_email = fake.generate_with_validation('email', lambda x: len(x) > 15)
print(f'有效邮箱: {valid_email}')

# 测试自定义Provider（示例：继承添加新方法）
class CustomFakerX(FakerX):
    def sku(self):
        return f'SKU-{self.pyint(min_value=1000, max_value=9999)}'

custom_fake = CustomFakerX('zh_CN')
sku = custom_fake.sku()
print(f'自定义SKU: {sku}')