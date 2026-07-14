# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:33
# @Software  : PyCharm
# @FileName  : test_faker_compatibility.py
# -----------------------------
"""
验证 FakerX 与原生 Faker 的完全兼容性
"""
import pytest
from faker import Faker
from faker.providers import BaseProvider
from fakerx import FakerX


class TestBasicCompatibility:
    """基础方法兼容性"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)
        self.faker = Faker('zh_CN')
        Faker.seed(42)

    @pytest.mark.parametrize("method", [
        'name', 'first_name', 'last_name', 'user_name',
        'email', 'phone_number', 'address', 'city',
        'text', 'sentence', 'word', 'paragraph',
        'date_time', 'date', 'time',
        'pyint', 'pyfloat', 'pystr', 'pybool',
        'boolean', 'uuid4', 'url', 'uri',
        'bothify', 'lexify', 'numerify',
        'random_element', 'random_int',
        'company', 'job', 'catch_phrase', 'bs',
        'credit_card_number', 'iban', 'swift',
        'color', 'hex_color', 'rgb_color',
        'file_name', 'file_path', 'mime_type',
        'isbn13', 'isbn10', 'ean', 'ean13', 'ean8',
        'locale', 'language_code', 'country_code',
    ])
    def test_method_returns_same_type(self, method):
        """所有原生方法都应该返回相同类型的结果"""
        fx_result = getattr(self.fake, method)()
        fk_result = getattr(self.faker, method)()
        assert type(fx_result) == type(fk_result), (
            f"{method}: FakerX 返回 {type(fx_result)}, "
            f"Faker 返回 {type(fk_result)}"
        )

    def test_method_with_args(self):
        """带参数的方法调用"""
        assert isinstance(self.fake.pyint(min_value=1, max_value=100), int)
        assert isinstance(self.fake.bothify(text='??-##'), str)
        assert isinstance(self.fake.text(max_nb_chars=50), str)

    def test_method_chaining(self):
        """方法链式调用"""
        name = self.fake.name()
        assert isinstance(name, str)
        assert len(name) > 0


class TestUniqueProxy:
    """unique 代理兼容性"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_unique_returns_unique_values(self):
        """unique 代理返回唯一值"""
        names = [self.fake.unique.name() for _ in range(50)]
        assert len(set(names)) == 50  # 全部唯一

    def test_unique_email(self):
        """unique email"""
        emails = [self.fake.unique.email() for _ in range(20)]
        assert len(set(emails)) == 20

    def test_unique_pyint(self):
        """unique pyint"""
        nums = [self.fake.unique.pyint(min_value=1, max_value=10000) for _ in range(50)]
        assert len(set(nums)) == 50


class TestSeedCompatibility:
    """种子机制兼容性"""

    def test_class_seed_reproducible(self):
        """FakerX.seed() 与 Faker.seed() 行为一致"""
        FakerX.seed(42)
        fx1 = FakerX('zh_CN')
        name1 = fx1.name()

        FakerX.seed(42)
        fx2 = FakerX('zh_CN')
        name2 = fx2.name()

        assert name1 == name2

    def test_instance_seed(self):
        """实例级种子"""
        fake1 = FakerX('zh_CN')
        FakerX.seed_instance(fake1, 42)
        name1 = fake1.name()

        fake2 = FakerX('zh_CN')
        FakerX.seed_instance(fake2, 42)
        name2 = fake2.name()

        assert name1 == name2

    def test_same_seed_same_result_as_faker(self):
        """相同种子下 FakerX 与 Faker 结果一致"""
        Faker.seed(42)
        faker = Faker('zh_CN')
        faker_name = faker.name()

        Faker.seed(42)
        fakerx = FakerX('zh_CN')
        fakerx_name = fakerx.name()

        assert faker_name == fakerx_name


class TestRandomAccess:
    """random 属性兼容性"""

    def setup_method(self):
        self.fake = FakerX('zh_CN')

    def test_random_instance(self):
        """可以访问底层 Random 实例"""
        import random as random_module
        assert isinstance(self.fake.random, random_module.Random)

    def test_random_method(self):
        """random 方法可用"""
        fake = FakerX('zh_CN')
        val = fake.random.randint(1, 100)
        assert 1 <= val <= 100


class TestProviderCompatibility:
    """Provider 系统兼容性"""

    def setup_method(self):
        self.fake = FakerX('zh_CN')

    def test_add_provider_class(self):
        """add_provider 注册完整的 Provider 类"""
        class MyProvider(BaseProvider):
            def my_custom_method(self):
                return 'custom_value'

            def random_choice_from_list(self, my_list):
                return self.random_element(my_list)

        self.fake.add_provider(MyProvider)

        assert self.fake.my_custom_method() == 'custom_value'
        assert self.fake.random_choice_from_list(['a', 'b', 'c']) in ['a', 'b', 'c']

    def test_add_provider_in_schema(self):
        """注册的 Provider 方法可在 Schema 中使用"""
        class ColorProvider(BaseProvider):
            def hex_color_upper(self):
                color = self.generator.hex_color()
                return color.upper()

        self.fake.add_provider(ColorProvider)

        data = self.fake.schema({
            'color': '{hex_color_upper}'
        }, iterations=5)

        for record in data:
            assert record['color'].startswith('#')
            assert record['color'] == record['color'].upper()

    def test_register_provider_function(self):
        """register_provider 注册单个函数"""
        def gen_phone_cn(faker, **kw):
            prefixes = ['138', '139', '150', '188']
            prefix = faker.random_element(prefixes)
            return prefix + ''.join(str(faker.random_digit()) for _ in range(8))

        self.fake.register_provider('phone_cn', gen_phone_cn)

        phone = self.fake.phone_cn()
        assert phone.startswith(('138', '139', '150', '188'))
        assert len(phone) == 11

    def test_register_provider_in_schema(self):
        """register_provider 注册的方法在 Schema 中可用"""
        def gen_biz_id(faker, **kw):
            return faker.bothify('BIZ-####-????')

        self.fake.register_provider('biz_id', gen_biz_id)

        data = self.fake.schema({
            'business_id': '{biz_id}'
        }, iterations=3)

        for record in data:
            assert record['business_id'].startswith('BIZ-')


class TestLocaleCompatibility:
    """Locale 兼容性"""

    def test_multiple_locales(self):
        """多 locale 实例独立"""
        fake_zh = FakerX('zh_CN')
        fake_en = FakerX('en_US')
        fake_ja = FakerX('ja_JP')

        # 各自能正常工作
        assert isinstance(fake_zh.name(), str)
        assert isinstance(fake_en.name(), str)
        assert isinstance(fake_ja.name(), str)

    def test_switch_locale(self):
        """切换 locale 后方法仍可用"""
        fake = FakerX('zh_CN')
        name_zh = fake.name()

        fake.switch_locale('en_US')
        name_en = fake.name()

        assert isinstance(name_zh, str)
        assert isinstance(name_en, str)

    def test_locale_specific_methods(self):
        """locale 特有的方法可用"""
        fake = FakerX('zh_CN')
        # zh_CN 特有的方法
        assert hasattr(fake, 'phone_number')
        result = fake.phone_number()
        assert isinstance(result, str)


class TestEdgeCases:
    """边界情况"""

    def test_dir_includes_faker_methods(self):
        """dir(fake) 包含 Faker 的方法"""
        fake = FakerX('zh_CN')
        all_attrs = dir(fake)
        assert 'name' in all_attrs
        assert 'email' in all_attrs
        assert 'pyint' in all_attrs

    def test_no_attribute_error_on_valid_method(self):
        """合法方法不报 AttributeError"""
        fake = FakerX('zh_CN')
        # 这些都是 Faker 内置方法
        for method in ['name', 'email', 'address', 'pyint']:
            result = getattr(fake, method)()
            assert result is not None

    def test_attribute_error_on_invalid_method(self):
        """不存在的方法报 AttributeError"""
        fake = FakerX('zh_CN')
        with pytest.raises(AttributeError):
            fake.nonexistent_method_xyz()

    def test_private_attribute_access(self):
        """私有属性正确报错而非递归"""
        fake = FakerX('zh_CN')
        with pytest.raises(AttributeError):
            fake._nonexistent_private
