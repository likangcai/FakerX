# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:15
# @Software  : PyCharm
# @FileName  : test_context.py
# -----------------------------
"""
上下文感知测试
"""

import pytest
from fakerx import FakerX
from fakerx.context import GenerationContext, parse_sequence_token


class TestGenerationContext:
    """GenerationContext 功能测试"""

    def setup_method(self):
        self.context = GenerationContext()

    def test_sequence_generation(self):
        """序列号生成"""
        # 序列号应该递增
        seq1 = self.context.sequence('test_seq')
        seq2 = self.context.sequence('test_seq')
        assert seq1 == 1
        assert seq2 == 2

    def test_sequence_with_start(self):
        """带起始值的序列号"""
        seq1 = self.context.sequence('test_seq', start=100)
        seq2 = self.context.sequence('test_seq', start=100)
        assert seq1 == 100
        assert seq2 == 101

    def test_sequence_with_step(self):
        """带步长的序列号"""
        seq1 = self.context.sequence('test_seq', start=1, step=2)
        seq2 = self.context.sequence('test_seq', start=1, step=2)
        assert seq1 == 1
        assert seq2 == 3

    def test_reset_sequence(self):
        """重置序列号"""
        self.context.sequence('test_seq')
        self.context.sequence('test_seq')
        assert self.context.sequence('test_seq') == 3

        self.context.reset_sequence('test_seq', start=1)
        assert self.context.sequence('test_seq') == 1

    def test_global_variables(self):
        """全局变量"""
        self.context.set_global('test_var', 'value1')
        assert self.context.get_global('test_var') == 'value1'
        assert self.context.get_global('nonexistent', 'default') == 'default'

    def test_add_record(self):
        """添加记录"""
        record1 = {'id': 1, 'name': 'test1'}
        record2 = {'id': 2, 'name': 'test2'}

        self.context.add_record(record1)
        self.context.add_record(record2)

        records = self.context.get_records()
        assert len(records) == 2
        assert records[0] == record1
        assert records[1] == record2

    def test_get_record(self):
        """按索引获取记录"""
        record1 = {'id': 1, 'name': 'test1'}
        record2 = {'id': 2, 'name': 'test2'}

        self.context.add_record(record1)
        self.context.add_record(record2)

        assert self.context.get_record(0) == record1
        assert self.context.get_record(1) == record2
        assert self.context.get_record(2) is None  # 超出范围

    def test_pick_from_records(self):
        """从记录中选取"""
        records = [
            {'id': 1, 'name': 'test1', 'city': 'Beijing'},
            {'id': 2, 'name': 'test2', 'city': 'Shanghai'},
            {'id': 3, 'name': 'test3', 'city': 'Guangzhou'},
        ]

        for record in records:
            self.context.add_record(record)

        # 随机选取
        city = self.context.pick_from_records('city')
        assert city in ['Beijing', 'Shanghai', 'Guangzhou']

        # 按策略选取
        city_first = self.context.pick_from_records('city', strategy='first')
        assert city_first == 'Beijing'

        city_last = self.context.pick_from_records('city', strategy='last')
        assert city_last == 'Guangzhou'

    def test_hooks(self):
        """生命周期钩子"""
        calls = []

        def before_hook(context, index):
            calls.append(('before', index))

        def after_hook(context, record, index):
            calls.append(('after', index, record['id']))

        self.context.add_hook('before_record', before_hook)
        self.context.add_hook('after_record', after_hook)

        self.context.run_hooks('before_record', 0)
        self.context.run_hooks('after_record', {'id': 1}, 0)

        assert len(calls) == 2
        assert calls[0] == ('before', 0)
        assert calls[1] == ('after', 0, 1)

    def test_reset(self):
        """重置上下文"""
        self.context.sequence('test_seq')
        self.context.set_global('test_var', 'value')
        self.context.add_record({'id': 1})

        self.context.reset()
        assert self.context.sequence('test_seq') == 1
        assert self.context.get_global('test_var') is None
        assert len(self.context.get_records()) == 0


class TestSequenceTokenParsing:
    """序列号 token 解析测试"""

    def test_parse_sequence_token(self):
        """解析序列号 token"""
        token = '{seq:test_seq}'
        result = parse_sequence_token(token)
        assert result == {'name': 'test_seq', 'start': 1, 'step': 1}

    def test_parse_sequence_with_start(self):
        """带起始值的序列号"""
        token = '{seq:test_seq:100}'
        result = parse_sequence_token(token)
        assert result == {'name': 'test_seq', 'start': 100, 'step': 1}

    def test_parse_sequence_with_step(self):
        """带步长的序列号"""
        token = '{seq:test_seq:1:2}'
        result = parse_sequence_token(token)
        assert result == {'name': 'test_seq', 'start': 1, 'step': 2}

    def test_invalid_token(self):
        """无效 token"""
        token = '{invalid_token}'
        result = parse_sequence_token(token)
        assert result is None


class TestContextInFakerX:
    """FakerX 中的上下文集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_context_property(self):
        """上下文属性"""
        assert hasattr(self.fake, 'context')
        assert isinstance(self.fake.context, GenerationContext)

    def test_sequence_in_schema(self):
        """Schema 中使用序列号"""
        schema = {
            'id': '{seq:user_id:1:1}',
            'name': '{name}',
        }

        data = self.fake.schema(schema, iterations=3)
        assert data[0]['id'] == 1
        assert data[1]['id'] == 2
        assert data[2]['id'] == 3

    def test_global_variables_in_schema(self):
        """Schema 中使用全局变量"""
        self.fake.context.set_global('company', 'Test Company')

        schema = {
            'id': '{pyint}',
            'company': '{global:company}',
        }

        data = self.fake.schema(schema, iterations=3)
        for record in data:
            assert record['company'] == 'Test Company'

    def test_cross_record_reference(self):
        """跨记录引用"""
        schema = {
            'id': '{seq:user_id:1:1}',
            'name': '{name}',
            'ref_id': {'ref': 'id'},
        }

        data = self.fake.schema(schema, iterations=3)
        for record in data:
            assert record['ref_id'] == record['id']

    def test_hooks_in_fakerx(self):
        """FakerX 中的钩子"""
        calls = []

        def before_hook(context, index):
            calls.append(('before', index))

        def after_hook(context, record, index):
            calls.append(('after', index, record['id']))

        self.fake.context.add_hook('before_record', before_hook)
        self.fake.context.add_hook('after_record', after_hook)

        self.fake.schema({'id': '{seq:test_id:1:1}', 'name': '{name}'}, iterations=2)

        assert len(calls) == 4  # 2 条记录 × 2 个钩子
        assert calls[0] == ('before', 0)
        assert calls[1] == ('after', 0, 1)
        assert calls[2] == ('before', 1)
        assert calls[3] == ('after', 1, 2)


class TestContextEdgeCases:
    """上下文边界情况"""

    def test_sequence_overflow(self):
        """序列号溢出"""
        context = GenerationContext()
        # 生成大量序列号
        for _ in range(1000):
            context.sequence('test_seq')
        # 应该还能继续生成
        assert context.sequence('test_seq') == 1001

    def test_record_reference(self):
        """记录引用"""
        context = GenerationContext()
        record1 = {'id': 1}
        record2 = {'id': 2}

        context.add_record(record1)
        context.add_record(record2)

        assert context.pick_from_records('id', strategy='first') == 1
        assert context.pick_from_records('id', strategy='last') == 2
        assert context.pick_from_records('id', strategy='round_robin') in [1, 2]


class TestContextPerformance:
    """上下文性能测试"""

    def test_sequence_performance(self):
        """序列号性能"""
        import time
        context = GenerationContext()
        start = time.time()
        for _ in range(10000):
            context.sequence('test_seq')
        duration = time.time() - start
        assert duration < 1.0  # 10000 次序列号生成应该在 1 秒内完成


class TestContextErrorHandling:
    """上下文错误处理"""

    def test_invalid_sequence_name(self):
        """无效序列号名称"""
        context = GenerationContext()
        with pytest.raises(Exception):
            context.sequence('')  # 空名称

    def test_record_reference_error(self):
        """记录引用错误"""
        context = GenerationContext()
        with pytest.raises(Exception):
            context.pick_from_records('nonexistent_field')
