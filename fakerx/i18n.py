# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:14
# @Software  : PyCharm
# @FileName  : i18n.py
# -----------------------------
"""
国际化支持 - 多 Locale、区域感知 Provider、Locale 切换
"""
import random
from typing import Dict, List, Optional, Any

from faker import Faker

# 支持的 locale 及其中文名称
SUPPORTED_LOCALES: Dict[str, str] = {
    'zh_CN': '简体中文',
    'zh_TW': '繁體中文',
    'en_US': 'English (US)',
    'en_GB': 'English (UK)',
    'ja_JP': '日本語',
    'ko_KR': '한국어',
    'fr_FR': 'Français',
    'de_DE': 'Deutsch',
    'es_ES': 'Español',
    'it_IT': 'Italiano',
    'pt_BR': 'Português (Brasil)',
    'ru_RU': 'Русский',
    'ar_SA': 'العربية',
    'hi_IN': 'हिन्दी',
    'th_TH': 'ไทย',
    'vi_VN': 'Tiếng Việt',
}

# 每个 locale 的特殊配置
LOCALE_CONFIG: Dict[str, Dict] = {
    'zh_CN': {
        'phone_format': r'1[3-9]\d{9}',
        'id_card_format': r'\d{17}[\dXx]',
        'zip_format': r'\d{6}',
        'currency': 'CNY',
        'currency_symbol': '¥',
        'date_format': '%Y-%m-%d',
    },
    'en_US': {
        'phone_format': r'\d{3}-\d{3}-\d{4}',
        'zip_format': r'\d{5}(-\d{4})?',
        'currency': 'USD',
        'currency_symbol': '$',
        'date_format': '%Y-%m-%d',
    },
    'ja_JP': {
        'phone_format': r'\d{2,4}-\d{2,4}-\d{4}',
        'zip_format': r'\d{3}-\d{4}',
        'currency': 'JPY',
        'currency_symbol': '¥',
        'date_format': '%Y年%m月%d日',
    },
    'fr_FR': {
        'phone_format': r'0\d{9}',
        'zip_format': r'\d{5}',
        'currency': 'EUR',
        'currency_symbol': '€',
        'date_format': '%d/%m/%Y',
    },
}


class I18nManager:
    """
    国际化管理器

    支持在运行时切换 locale，多 locale 混合生成

    Example:
        >>> i18n = I18nManager(['zh_CN', 'en_US'])
        >>> i18n.faker('zh_CN').name()  # 中文名
        >>> i18n.faker('en_US').name()  # 英文名
        >>> i18n.switch('ja_JP')        # 切换主 locale
    """

    def __init__(self, locales: Optional[List[str]] = None,
                 default_locale: str = 'zh_CN'):
        """
        Args:
            locales: 支持的 locale 列表
            default_locale: 默认 locale
        """
        self._locales = locales or [default_locale]
        if default_locale not in self._locales:
            self._locales.insert(0, default_locale)
        self._default = default_locale
        self._fakers: Dict[str, Faker] = {}
        self._current = default_locale
        self._validate_locales()
        self._init_fakers()

    def _validate_locales(self):
        """验证 locale 是否有效"""
        for locale in self._locales:
            if locale not in SUPPORTED_LOCALES:
                raise ValueError(f"不支持的 locale: '{locale}'。支持的 locale: {', '.join(SUPPORTED_LOCALES.keys())}")

    def _init_fakers(self):
        """初始化所有 locale 的 Faker 实例"""
        for locale in self._locales:
            if locale not in self._fakers:
                try:
                    self._fakers[locale] = Faker(locale)
                except Exception:
                    # 尝试回退到 en_US
                    try:
                        self._fakers[locale] = Faker('en_US')
                    except Exception as e:
                        raise ValueError(f"无法创建 locale '{locale}' 的 Faker 实例: {e}")

    def faker(self, locale: Optional[str] = None) -> Faker:
        """获取指定 locale 的 Faker 实例"""
        loc = locale or self._current
        if loc not in self._fakers:
            self._fakers[loc] = Faker(loc)
        return self._fakers[loc]

    def switch(self, locale: str):
        """切换当前 locale"""
        if locale not in SUPPORTED_LOCALES:
            raise ValueError(f"不支持的 locale: '{locale}'。支持的 locale: {', '.join(SUPPORTED_LOCALES.keys())}")
        if locale not in self._fakers:
            self._fakers[locale] = Faker(locale)
        self._current = locale

    @property
    def current(self) -> str:
        """当前 locale"""
        return self._current

    @property
    def available_locales(self) -> List[str]:
        """已加载的 locale 列表"""
        return list(self._fakers.keys())

    def config(self, locale: Optional[str] = None) -> Dict:
        """获取 locale 的配置信息"""
        loc = locale or self._current
        return LOCALE_CONFIG.get(loc, LOCALE_CONFIG.get('en_US', {}))

    def generate_localized(
            self,
            schema: Dict,
            iterations: int = 1,
            locale_weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict]:
        """
        多 locale 混合生成

        Args:
            schema: Schema 定义
            iterations: 总条数
            locale_weights: 各 locale 的权重
                {'zh_CN': 0.7, 'en_US': 0.3}

        Example:
            >>> data = i18n.generate_localized(
            ...     {'name': '{name}', 'city': '{city}'},
            ...     iterations=100,
            ...     locale_weights={'zh_CN': 0.6, 'en_US': 0.4}
            ... )
            # 60% 中文数据, 40% 英文数据
        """
        import random

        if locale_weights is None:
            locale_weights = {self._default: 1.0}

        locales = list(locale_weights.keys())
        weights = list(locale_weights.values())

        results = []
        for _ in range(iterations):
            locale = random.choices(locales, weights=weights, k=1)[0]
            fake = self.faker(locale)

            record = {}
            for key, field_def in schema.items():
                record[key] = self._generate_field(fake, key, field_def)
            # 添加 locale 元数据
            record['_locale'] = locale
            results.append(record)

        return results

    def _generate_field(self, fake, key, field_def):
        """简单字段生成"""
        import re
        if isinstance(field_def, str):
            match = re.match(r'^\{(\w+)\}$', field_def)
            if match:
                method = getattr(fake, match.group(1), None)
                if method:
                    return method()
        elif isinstance(field_def, dict):
            if 'elements' in field_def:
                return random.choice(field_def['elements'])
            if 'method' in field_def:
                method = getattr(fake, field_def['method'], None)
                if method:
                    kwargs = {k: v for k, v in field_def.items()
                              if k not in ('method', 'elements', 'weights')}
                    return method(**kwargs) if kwargs else method()
        elif isinstance(field_def, list):
            return random.choice(field_def)
        return field_def

    @staticmethod
    def list_supported_locales() -> Dict[str, str]:
        """列出所有支持的 locale"""
        return SUPPORTED_LOCALES.copy()
