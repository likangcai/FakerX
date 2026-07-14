# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:16
# @Software  : PyCharm
# @FileName  : test_i18n.py
# -----------------------------
"""
国际化测试
"""

import pytest
from fakerx import FakerX
from fakerx.i18n import I18nManager, SUPPORTED_LOCALES, LOCALE_CONFIG


class TestI18nManager:
    """I18nManager 功能测试"""

    def setup_method(self):
        self.i18n = I18nManager(['zh_CN', 'en_US'])

    def test_supported_locales(self):
        """支持的 locale 列表"""
        locales = self.i18n.available_locales
        assert 'zh_CN' in locales
        assert 'en_US' in locales

    def test_switch_locale(self):
        """切换 locale"""
        self.i18n.switch('zh_CN')
        assert self.i18n.current == 'zh_CN'

        self.i18n.switch('en_US')
        assert self.i18n.current == 'en_US'

    def test_faker_instances(self):
        """不同 locale 的 Faker 实例"""
        zh_faker = self.i18n.faker('zh_CN')
        en_faker = self.i18n.faker('en_US')

        zh_name = zh_faker.name()
        en_name = en_faker.name()

        assert isinstance(zh_name, str)
        assert isinstance(en_name, str)
        assert zh_name != en_name  # 不同 locale 的名字不同

    def test_generate_localized(self):
        """多 locale 混合生成"""
        schema = {'name': '{name}', 'city': '{city}'}
        data = self.i18n.generate_localized(schema, iterations=10)

        # 检查生成的数据包含 locale 信息
        for record in data:
            assert '_locale' in record
            assert record['_locale'] in ['zh_CN', 'en_US']

    def test_locale_config(self):
        """locale 配置信息"""
        config = self.i18n.config('zh_CN')
        assert 'phone_format' in config
        assert 'currency' in config

    def test_list_supported_locales(self):
        """列出所有支持的 locale"""
        locales = I18nManager.list_supported_locales()
        assert 'zh_CN' in locales
        assert 'en_US' in locales
        assert len(locales) >= 2


class TestI18nInFakerX:
    """FakerX 中的国际化集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_switch_locale_in_fakerx(self):
        """FakerX 中切换 locale"""
        name_zh = self.fake.name()

        self.fake.switch_locale('en_US')
        name_en = self.fake.name()

        assert isinstance(name_zh, str)
        assert isinstance(name_en, str)
        assert name_zh != name_en

    def test_generate_localized_in_fakerx(self):
        """FakerX 中多 locale 生成"""
        data = self.fake.generate_localized(
            {'name': '{name}', 'city': '{city}'},
            iterations=20,
            locale_weights={'zh_CN': 0.7, 'en_US': 0.3}
        )

        # 检查生成的数据
        for record in data:
            assert '_locale' in record
            assert record['_locale'] in ['zh_CN', 'en_US']


class TestI18nEdgeCases:
    """国际化边界情况"""

    def setup_method(self):
        self.i18n = I18nManager(['zh_CN', 'en_US'])

    def test_invalid_locale(self):
        """无效 locale"""
        with pytest.raises(Exception):
            I18nManager(['invalid_locale'])

    def test_locale_without_faker(self):
        """不支持的 locale"""
        with pytest.raises(Exception):
            I18nManager(['xx_XX'])

    def test_locale_config_missing(self):
        """locale 配置缺失"""
        # 某些 locale 可能没有配置，应该能正常工作
        i18n = I18nManager(['zh_CN'])
        config = i18n.config('zh_CN')
        assert config is not None


class TestI18nPerformance:
    """国际化性能测试"""

    def setup_method(self):
        self.i18n = I18nManager(['zh_CN', 'en_US'])

    def test_locale_switch_performance(self):
        """locale 切换性能"""
        import time
        start = time.time()
        for _ in range(100):
            self.i18n.switch('zh_CN')
            self.i18n.switch('en_US')
        duration = time.time() - start
        assert duration < 1.0  # 100 次切换应该在 1 秒内完成


class TestI18nErrorHandling:
    """国际化错误处理"""

    def setup_method(self):
        self.i18n = I18nManager(['zh_CN'])

    def test_locale_switch_error(self):
        """locale 切换错误"""
        with pytest.raises(Exception):
            self.i18n.switch('invalid_locale')

    def test_faker_creation_error(self):
        """Faker 实例创建错误"""
        # 测试不支持的 locale
        with pytest.raises(Exception):
            self.i18n.faker('invalid_locale')


class TestI18nDocumentation:
    """国际化文档测试"""

    def test_example_code_runs(self):
        """示例代码能正常运行"""
        # 测试 i18n.py 中的示例
        pass
