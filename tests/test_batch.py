# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:16
# @Software  : PyCharm
# @FileName  : test_batch.py
# -----------------------------
"""
批处理测试
"""

import pytest
import os
import tempfile
from fakerx import FakerX
from fakerx.batch import (
    BatchGenerator, GenerationCache, MappedWriter
)
from fakerx.exceptions import FakerXError


class TestBatchGenerator:
    """BatchGenerator 功能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_generate_parallel(self):
        """多进程并行生成"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}
        data = BatchGenerator.generate_parallel(schema, total_count=100, workers=4)

        assert len(data) == 100
        for record in data:
            assert 'id' in record
            assert 'name' in record

    def test_generate_parallel_stream(self):
        """多进程并行流式生成"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}
        generator = BatchGenerator.generate_parallel_stream(
            schema, total_count=100, workers=4
        )

        count = 0
        for _ in generator:
            count += 1
        assert count == 100

    def test_generate_async(self):
        """异步生成"""
        import asyncio
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}

        async def test_async():
            data = await BatchGenerator.generate_async(schema, total_count=100)
            assert len(data) == 100

        asyncio.run(test_async())

    def test_generate_async_stream(self):
        """异步流式生成"""
        import asyncio
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}

        async def test_async_stream():
            generator = BatchGenerator.generate_async_stream(schema, total_count=100)
            count = 0
            async for _ in generator:
                count += 1
            assert count == 100

        asyncio.run(test_async_stream())


class TestGenerationCache:
    """生成缓存测试"""

    def setup_method(self):
        self.cache = GenerationCache()

    def test_get_or_generate(self):
        """获取或生成数据"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}

        # 第一次生成
        data1 = self.cache.get_or_generate(schema, 10)
        assert len(data1) == 10

        # 第二次应该从缓存获取
        data2 = self.cache.get_or_generate(schema, 10)
        assert data1 == data2  # 相同数据

        # 不同参数，不同数据
        data3 = self.cache.get_or_generate(schema, 5)
        assert len(data3) == 5
        assert data3 != data1

    def test_cache_stats(self):
        """缓存统计"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}
        self.cache.get_or_generate(schema, 10)
        self.cache.get_or_generate(schema, 5)

        stats = self.cache.stats()
        assert stats['entries'] == 2
        assert stats['total_records'] == 15

    def test_cache_clear(self):
        """清空缓存"""
        schema = {'id': {'method': 'pyint'}, 'name': '{name}'}
        self.cache.get_or_generate(schema, 10)

        self.cache.clear()
        stats = self.cache.stats()
        assert stats['entries'] == 0
        assert stats['total_records'] == 0


class TestMappedWriter:
    """MappedWriter 测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_write_and_flush(self):
        """写入和刷新"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            filepath = f.name

        writer = MappedWriter(chunk_size=100)
        for _ in range(250):  # 250 条数据，分成 3 个 chunk
            writer.write({'id': self.fake.pyint(), 'name': self.fake.name()})

        writer.flush_to_csv(filepath)

        assert os.path.exists(filepath)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1  # 至少 header + 数据

        os.remove(filepath)

    def test_write_batch(self):
        """批量写入"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            filepath = f.name

        writer = MappedWriter(chunk_size=100)
        batch = [{'id': self.fake.pyint(), 'name': self.fake.name()} for _ in range(250)]
        writer.write_batch(batch)
        writer.flush_to_csv(filepath)

        assert os.path.exists(filepath)
        os.remove(filepath)

    def test_iter_records(self):
        """迭代记录"""
        writer = MappedWriter(chunk_size=100)
        for _ in range(250):
            writer.write({'id': self.fake.pyint(), 'name': self.fake.name()})

        count = 0
        for record in writer.iter_records():
            count += 1
            assert 'id' in record
            assert 'name' in record

        assert count == 250

    def test_cleanup(self):
        """清理"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
            filepath = f.name

        writer = MappedWriter(chunk_size=100)
        writer.write({'id': 1, 'name': 'test'})
        writer.flush_to_csv(filepath)

        writer.cleanup()
        assert not os.path.exists(filepath)  # 临时文件应该被删除


class TestBatchInFakerX:
    """FakerX 中的批处理集成测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_schema_parallel(self):
        """FakerX 中多进程生成"""
        data = self.fake.schema_parallel(
            {'id': {'method': 'pyint'}, 'name': '{name}'},
            total_count=100,
            workers=4
        )
        assert len(data) == 100

    def test_schema_async(self):
        """FakerX 中异步生成"""
        import asyncio
        async def test_async():
            data = await self.fake.schema_async(
                {'id': {'method': 'pyint'}, 'name': '{name}'},
                total_count=100
            )
            assert len(data) == 100

        asyncio.run(test_async())

    def test_large_dataset(self):
        """大数据集生成"""
        # 生成 10000 条数据
        data = self.fake.schema_parallel(
            {'id': {'method': 'pyint'}, 'name': '{name}'},
            total_count=10000,
            workers=8
        )
        assert len(data) == 10000


class TestBatchEdgeCases:
    """批处理边界情况"""

    def test_zero_count(self):
        """零条数据"""
        data = BatchGenerator.generate_parallel(
            {'id': {'method': 'pyint'}}, total_count=0, workers=4
        )
        assert len(data) == 0

    def test_single_worker(self):
        """单工作进程"""
        data = BatchGenerator.generate_parallel(
            {'id': {'method': 'pyint'}}, total_count=100, workers=1
        )
        assert len(data) == 100

    def test_large_chunk_size(self):
        """大 chunk 大小"""
        data = BatchGenerator.generate_parallel(
            {'id': {'method': 'pyint'}}, total_count=100, workers=4, chunk_size=1000
        )
        assert len(data) == 100


class TestBatchPerformance:
    """批处理性能测试"""

    def setup_method(self):
        self.fake = FakerX('zh_CN', seed=42)

    def test_parallel_performance(self):
        """并行性能"""
        import time
        start = time.time()
        data = self.fake.schema_parallel(
            {'id': {'method': 'pyint'}, 'name': '{name}'},
            total_count=10000,
            workers=4
        )
        duration = time.time() - start
        assert len(data) == 10000
        assert duration < 10.0  # 10000 条数据应该在 10 秒内完成


class TestBatchErrorHandling:
    """批处理错误处理"""

    def test_invalid_schema(self):
        """无效 Schema"""
        with pytest.raises(FakerXError):
            BatchGenerator.generate_parallel(
                {'invalid': 'schema'}, total_count=10, workers=4
            )

    def test_negative_count(self):
        """负条数"""
        with pytest.raises(ValueError):
            BatchGenerator.generate_parallel(
                {'id': {'method': 'pyint'}}, total_count=-1, workers=4
            )

    def test_zero_workers(self):
        """零工作进程"""
        with pytest.raises(ValueError):
            BatchGenerator.generate_parallel(
                {'id': {'method': 'pyint'}}, total_count=10, workers=0
            )
