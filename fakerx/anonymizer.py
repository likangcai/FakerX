# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 14:54
# @Software  : PyCharm
# @FileName  : anonymizer.py
# -----------------------------
"""
数据脱敏模块 - 对真实数据进行匿名化处理
"""

import re
from typing import Dict, List, Any, Optional


class DataAnonymizer:
    """数据脱敏器"""

    # 字段类型自动推断规则
    AUTO_PATTERNS = {
        'phone': r'^1[3-9]\d{9}$',
        'email': r'^[\w.+-]+@[\w-]+\.[\w.-]+$',
        'id_card': r'^\d{17}[\dXx]$',
        'bank_card': r'^\d{16,19}$',
    }

    @classmethod
    def anonymize(cls, value: str, field_type: str = 'auto', **kwargs) -> str:
        """
        对单个值进行脱敏

        Args:
            value: 原始值
            field_type: 脱敏类型
                'phone' - 手机号: 138****1234
                'email' - 邮箱: z***@example.com
                'id_card' - 身份证: 110101********1234
                'name' - 姓名: 张**
                'address' - 地址: 北京市朝阳区****
                'bank_card' - 银行卡: 6222 **** **** 1234
                'auto' - 自动识别类型
        """
        if value is None:
            return None

        value = str(value)

        if field_type == 'auto':
            field_type = cls._detect_type(value)

        handlers = {
            'phone': cls._anon_phone,
            'email': cls._anon_email,
            'id_card': cls._anon_id_card,
            'name': cls._anon_name,
            'address': cls._anon_address,
            'bank_card': cls._anon_bank_card,
        }

        handler = handlers.get(field_type, cls._anon_default)
        return handler(value, **kwargs)

    @classmethod
    def anonymize_dict(
            cls,
            data: Dict,
            field_mapping: Dict[str, str],
    ) -> Dict:
        """
        对字典数据进行批量脱敏

        Args:
            data: 原始数据字典
            field_mapping: 字段名 -> 脱敏类型 映射
                {'phone': 'phone', 'email': 'email'}

        Example:
            >>> data = {'name': '张三', 'phone': '13812345678'}
            >>> DataAnonymizer.anonymize_dict(data, {'phone': 'phone'})
            {'name': '张三', 'phone': '138****5678'}
        """
        result = {}
        for key, value in data.items():
            if key in field_mapping:
                result[key] = cls.anonymize(value, field_mapping[key])
            else:
                result[key] = value
        return result

    @classmethod
    def anonymize_list(
            cls,
            data: List[Dict],
            field_mapping: Dict[str, str],
    ) -> List[Dict]:
        """对列表中的每条记录进行脱敏"""
        return [cls.anonymize_dict(row, field_mapping) for row in data]

    @classmethod
    def _detect_type(cls, value: str) -> str:
        """自动识别数据类型"""
        for ftype, pattern in cls.AUTO_PATTERNS.items():
            if re.match(pattern, value):
                return ftype
        return 'default'

    @staticmethod
    def _anon_phone(value: str, **kw) -> str:
        """手机号脱敏: 138****1234"""
        return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', value)

    @staticmethod
    def _anon_email(value: str, **kw) -> str:
        """邮箱脱敏: z***@example.com"""
        parts = value.split('@')
        if len(parts) == 2:
            name = parts[0]
            masked = name[0] + '*' * (len(name) - 1) if len(name) > 1 else '*'
            return f"{masked}@{parts[1]}"
        return value

    @staticmethod
    def _anon_id_card(value: str, **kw) -> str:
        """身份证脱敏: 110101********1234"""
        if len(value) >= 14:
            return value[:6] + '*' * 8 + value[-4:]
        return value

    @staticmethod
    def _anon_name(value: str, **kw) -> str:
        """姓名脱敏: 张**"""
        if len(value) <= 1:
            return value
        return value[0] + '*' * (len(value) - 1)

    @staticmethod
    def _anon_address(value: str, **kw) -> str:
        """地址脱敏: 北京市朝阳区****"""
        match = re.match(r'^(.+?[省市].+?[区县])', value)
        if match:
            return match.group(1) + '****'
        return '****'

    @staticmethod
    def _anon_bank_card(value: str, **kw) -> str:
        """银行卡脱敏: 6222 **** **** 1234"""
        digits = re.sub(r'\D', '', value)
        if len(digits) >= 8:
            return f"{digits[:4]} **** **** {digits[-4:]}"
        return value

    @staticmethod
    def _anon_default(value: str, **kw) -> str:
        """默认脱敏: 保留首尾，中间替换"""
        if len(value) > 4:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]
        return '****'
