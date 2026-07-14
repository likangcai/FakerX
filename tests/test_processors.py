# -*- coding: utf-8 -*-
"""数据处理模块测试"""
import pytest
from fakerx.processors import PostProcessor


class TestPostProcessor:
    """PostProcessor 功能测试"""

    def setup_method(self):
        self.pp = PostProcessor()

    def test_upper(self):
        assert self.pp.process_field('hello', ['upper']) == 'HELLO'

    def test_lower(self):
        assert self.pp.process_field('HELLO', ['lower']) == 'hello'

    def test_strip(self):
        assert self.pp.process_field('  hello  ', ['strip']) == 'hello'

    def test_title(self):
        assert self.pp.process_field('hello world', ['title']) == 'Hello World'

    def test_md5(self):
        result = self.pp.process_field('test', ['md5'])
        assert len(result) == 32
        assert isinstance(result, str)

    def test_sha256(self):
        result = self.pp.process_field('test', ['sha256'])
        assert len(result) == 64

    def test_round2(self):
        assert self.pp.process_field(3.14159, ['round2']) == 3.14

    def test_round4(self):
        assert self.pp.process_field(3.14159, ['round4']) == 3.1416

    def test_to_int(self):
        assert self.pp.process_field('42', ['to_int']) == 42

    def test_to_str(self):
        assert self.pp.process_field(42, ['to_str']) == '42'

    def test_to_float(self):
        assert self.pp.process_field('3.14', ['to_float']) == 3.14

    def test_chain_processors(self):
        assert self.pp.process_field('  Hello  ', ['strip', 'upper']) == 'HELLO'

    def test_process_record(self):
        record = {'name': '  zhang  ', 'price': '12.345'}
        result = self.pp.process_record(record, {'name': ['strip', 'title'], 'price': ['round2']})
        assert result['name'] == 'Zhang'
        assert result['price'] == 12.35

    def test_process_records(self):
        records = [{'name': '  alice  '}, {'name': '  bob  '}]
        result = self.pp.process_records(records, {'name': ['strip', 'upper']})
        assert result[0]['name'] == 'ALICE'
        assert result[1]['name'] == 'BOB'

    def test_register_custom_processor(self):
        self.pp.register('double', lambda v: v * 2 if v else v)
        assert self.pp.process_field(5, ['double']) == 10

    def test_unknown_processor(self):
        with pytest.raises(ValueError):
            self.pp.process_field('test', ['unknown'])

    def test_deduplicate_by_first(self):
        records = [{'id': 1}, {'id': 2}, {'id': 1}]
        result = self.pp.deduplicate(records, ['id'], keep='first')
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['id'] == 2

    def test_deduplicate_by_last(self):
        records = [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}, {'id': 1, 'v': 'c'}]
        result = self.pp.deduplicate(records, ['id'], keep='last')
        assert len(result) == 2
        assert result[0]['v'] == 'c'  # 保留最后一条