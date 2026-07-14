# -*- coding: utf-8 -*-
"""数据脱敏模块测试"""
import pytest
from fakerx.anonymizer import DataAnonymizer


class TestDataAnonymizer:
    """DataAnonymizer 功能测试"""

    def test_phone_anonymize(self):
        assert DataAnonymizer.anonymize('13812345678', 'phone') == '138****5678'

    def test_email_anonymize(self):
        result = DataAnonymizer.anonymize('zhangsan@gmail.com', 'email')
        assert result.startswith('z')
        assert '@gmail.com' in result
        assert '*' in result

    def test_id_card_anonymize(self):
        result = DataAnonymizer.anonymize('110101199001011234', 'id_card')
        assert result.startswith('110101')
        assert result.endswith('1234')
        assert '********' in result

    def test_name_anonymize(self):
        assert DataAnonymizer.anonymize('张三', 'name') == '张*'

    def test_address_anonymize(self):
        result = DataAnonymizer.anonymize('北京市朝阳区建国路88号', 'address')
        assert '****' in result

    def test_bank_card_anonymize(self):
        result = DataAnonymizer.anonymize('6222021234561234', 'bank_card')
        assert '****' in result

    def test_auto_detect_phone(self):
        assert DataAnonymizer.anonymize('13812345678') == '138****5678'

    def test_auto_detect_email(self):
        result = DataAnonymizer.anonymize('test@example.com')
        assert '@' in result
        assert '*' in result

    def test_anonymize_dict(self):
        data = {'name': '张三', 'phone': '13812345678'}
        result = DataAnonymizer.anonymize_dict(data, {'phone': 'phone', 'name': 'name'})
        assert result['name'] == '张*'
        assert '****' in result['phone']

    def test_anonymize_list(self):
        data = [{'phone': '13812345678'}, {'phone': '13912345678'}]
        result = DataAnonymizer.anonymize_list(data, {'phone': 'phone'})
        for r in result:
            assert '****' in r['phone']

    def test_none_value(self):
        assert DataAnonymizer.anonymize(None, 'phone') is None

    def test_default_anonymize(self):
        result = DataAnonymizer.anonymize('longstringvalue', 'default')
        assert '*' in result