# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:14
# @Software  : PyCharm
# @FileName  : batch.py
# -----------------------------
"""
高性能批处理引擎 - 多进程、异步、内存映射、缓存
"""

import os
import time
import json
import csv
import pickle
import hashlib
from typing import Dict, List, Optional, Generator, Callable, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import partial


# ----------------------------------------------------------------
# 多进程批处理
# ----------------------------------------------------------------

def _worker_generate(args):
    """子进程工作函数（必须在模块顶层，可被 pickle）"""
    schema, count, worker_id, seed, unique_fields = args

    from faker import Faker
    fake = Faker()
    if seed is not None:
        Faker.seed(seed + worker_id)

    results = []
    seen = {f: set() for f in (unique_fields or [])}

    for i in range(count):
        record = {}
        for key, field_def in schema.items():
            value = _generate_field(fake, key, field_def, record, seen)
            record[key] = value
        results.append(record)

    return results


def _generate_field(fake, key, field_def, context, seen):
    """子进程内的字段生成"""
    import random
    import re

    if isinstance(field_def, str):
        method_match = re.match(r'^\{(\w+)\}$', field_def)
        if method_match:
            method = getattr(fake, method_match.group(1), None)
            if method:
                return method()
        return field_def

    if isinstance(field_def, dict):
        if 'elements' in field_def:
            elements = field_def['elements']
            weights = field_def.get('weights')
            if weights:
                return random.choices(elements, weights=weights, k=1)[0]
            return random.choice(elements)

        if 'method' in field_def:
            method_name = field_def['method']
            special_keys = {'method', 'elements', 'weights', 'unique'}
            kwargs = {k: v for k, v in field_def.items() if k not in special_keys}

            method = getattr(fake, method_name, None)
            if method:
                if key in seen:
                    for _ in range(100):
                        val = method(**kwargs) if kwargs else method()
                        if val not in seen[key]:
                            seen[key].add(val)
                            return val
                    return val
                return method(**kwargs) if kwargs else method()

        # 嵌套 dict
        return {k: _generate_field(fake, k, v, context, seen)
                for k, v in field_def.items()}

    if isinstance(field_def, list):
        return random.choice(field_def)

    return field_def


def _validate_schema(schema: Dict) -> None:
    """校验 schema 合法性"""
    if not isinstance(schema, dict):
        from .exceptions import FakerXError
        raise FakerXError("Schema 必须是 dict")
    for key, field_def in schema.items():
        if field_def is None:
            from .exceptions import FakerXError
            raise FakerXError(f"字段 '{key}' 的定义为空")
        if isinstance(field_def, str):
            if not field_def.startswith('{') or not field_def.endswith('}'):
                from .exceptions import FakerXError
                raise FakerXError(f"字段 '{key}': 无效的字符串定义 '{field_def}'，"
                                  f"应为 '{{method_name}}' 格式")
        elif isinstance(field_def, dict):
            if 'method' not in field_def and 'elements' not in field_def and 'if' not in field_def:
                from .exceptions import FakerXError
                raise FakerXError(f"字段 '{key}': dict 定义必须包含 'method'、'elements' 或 'if'")


class BatchGenerator:
    """
    高性能批处理生成器

    支持三种模式:
    1. 单进程流式 (默认，内存友好)
    2. 多进程并行 (CPU 密集型场景)
    3. 异步生成 (IO 密集型场景)
    """

    @staticmethod
    def generate_parallel(
            schema: Dict,
            total_count: int,
            workers: int = 4,
            unique_fields: Optional[List[str]] = None,
            base_seed: Optional[int] = None,
            chunk_size: Optional[int] = None,
    ) -> List[Dict]:
        """
        多进程并行生成

        Args:
            schema: Schema 定义
            total_count: 总生成条数
            workers: 进程数
            unique_fields: 唯一字段（注意：多进程模式下唯一性仅在同一进程内保证）
            base_seed: 随机种子基数（每个进程使用不同种子）

        Example:
            >>> data = BatchGenerator.generate_parallel(
            ...     {'id': {'method': 'pyint'}, 'name': '{name}'},
            ...     total_count=100000,
            ...     workers=8
            ... )
        """
        if workers <= 0:
            raise ValueError("workers 必须大于 0")
        if total_count < 0:
            raise ValueError("total_count 不能为负")
        if total_count == 0:
            return []

        _validate_schema(schema)

        # 单 worker 或小数据量退化为单进程
        if workers == 1 or total_count < workers:
            from faker import Faker
            fake = Faker()
            if base_seed is not None:
                Faker.seed(base_seed)
            seen = {f: set() for f in (unique_fields or [])}
            results = []
            for _ in range(total_count):
                record = {}
                for key, field_def in schema.items():
                    record[key] = _generate_field(fake, key, field_def, record, seen)
                results.append(record)
            return results

        chunk_size = total_count // workers
        remainder = total_count % workers

        tasks = []
        for i in range(workers):
            seed = base_seed + i if base_seed is not None else None
            end = (i + 1) * chunk_size + (1 if i < remainder else 0)
            start = i * chunk_size + min(i, remainder)
            count = end - start
            if count > 0:
                tasks.append((schema, count, i, seed, unique_fields))

        results: List[Dict] = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_worker_generate, task) for task in tasks]
            for future in as_completed(futures):
                results.extend(future.result())

        return results

    @staticmethod
    def generate_parallel_stream(
            schema: Dict,
            total_count: int,
            workers: int = 4,
            unique_fields: Optional[List[str]] = None,
            base_seed: Optional[int] = None,
    ) -> Generator[Dict, None, None]:
        """
        多进程并行流式生成

        与 generate_parallel 类似，但以生成器形式逐条 yield，
        避免一次性收集所有结果占用内存。
        """
        if workers <= 0:
            raise ValueError("workers 必须大于 0")
        if total_count < 0:
            raise ValueError("total_count 不能为负")
        if total_count == 0:
            return

        _validate_schema(schema)

        chunk_size = total_count // workers
        remainder = total_count % workers

        tasks = []
        for i in range(workers):
            seed = base_seed + i if base_seed is not None else None
            end = (i + 1) * chunk_size + (1 if i < remainder else 0)
            start = i * chunk_size + min(i, remainder)
            count = end - start
            if count > 0:
                tasks.append((schema, count, i, seed, unique_fields))

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_worker_generate, task) for task in tasks]
            for future in as_completed(futures):
                for record in future.result():
                    yield record

    @staticmethod
    async def generate_async(
            schema: Dict,
            total_count: int,
            batch_size: int = 100,
    ) -> List[Dict]:
        """
        异步生成（适合 IO 密集型场景）

        将 total_count 拆分为多个 batch，每个 batch 在线程池中并行生成。
        """
        import asyncio

        if total_count < 0:
            raise ValueError("total_count 不能为负")
        if batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")
        if total_count == 0:
            return []

        _validate_schema(schema)

        num_batches = (total_count + batch_size - 1) // batch_size
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async def _gen_batch(batch_idx: int) -> List[Dict]:
            start = batch_idx * batch_size
            end = min(start + batch_size, total_count)
            count = end - start
            return await loop.run_in_executor(
                None,
                lambda: BatchGenerator.generate_parallel(schema, count, workers=1)
            )

        tasks = [_gen_batch(i) for i in range(num_batches)]
        batches = await asyncio.gather(*tasks)
        results = []
        for batch in batches:
            results.extend(batch)
        return results

    @staticmethod
    async def generate_async_stream(
            schema: Dict,
            total_count: int,
            batch_size: int = 100,
    ):
        """
        异步流式生成

        以异步生成器形式逐条 yield，内存占用恒定。
        """
        import asyncio

        if total_count < 0:
            raise ValueError("total_count 不能为负")
        if batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")
        if total_count == 0:
            return

        _validate_schema(schema)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        num_batches = (total_count + batch_size - 1) // batch_size

        for batch_idx in range(num_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total_count)
            count = end - start
            batch = await loop.run_in_executor(
                None,
                lambda c=count: BatchGenerator.generate_parallel(schema, c, workers=1)
            )
            for record in batch:
                yield record


# ----------------------------------------------------------------
# 生成缓存
# ----------------------------------------------------------------

class GenerationCache:
    """
    生成缓存

    缓存已生成的数据，相同 schema + count 直接返回缓存结果，
    避免重复生成。适用于测试 fixtures、重复演示等场景。
    """

    def __init__(self):
        self._cache: Dict[str, List[Dict]] = {}
        self._lock = __import__('threading').Lock()

    @staticmethod
    def _make_key(schema: Dict, count: int) -> str:
        """根据 schema 和 count 生成缓存键"""
        try:
            schema_str = json.dumps(schema, sort_keys=True, default=str)
        except (TypeError, ValueError):
            schema_str = str(schema)
        return hashlib.md5(f"{schema_str}:{count}".encode('utf-8')).hexdigest()

    def get_or_generate(self, schema: Dict, count: int) -> List[Dict]:
        """
        获取或生成数据

        如果缓存中已有相同 schema + count 的数据，直接返回；
        否则生成新数据并存入缓存。
        """
        key = self._make_key(schema, count)
        with self._lock:
            if key in self._cache:
                return self._cache[key]

        # 在锁外生成，避免长时间持锁
        from .fakerx import FakerX
        fake = FakerX()
        data = fake.schema(schema, iterations=count)

        with self._lock:
            self._cache[key] = data
        return data

    def stats(self) -> Dict[str, int]:
        """缓存统计"""
        with self._lock:
            return {
                'entries': len(self._cache),
                'total_records': sum(len(v) for v in self._cache.values()),
            }

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


# ----------------------------------------------------------------
# 内存映射写入器
# ----------------------------------------------------------------

class MappedWriter:
    """
    内存映射写入器

    将生成数据分 chunk 持久化到内存列表，按需迭代读取，
    适用于超大数据集场景，内存占用可控。
    """

    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self._chunks: List[List[Dict]] = []
        self._current_chunk: List[Dict] = []
        self._last_output_path: Optional[str] = None
        self._total_records = 0

    def write(self, record: Dict) -> None:
        """写入单条记录"""
        self._current_chunk.append(record)
        self._total_records += 1
        if len(self._current_chunk) >= self.chunk_size:
            self._flush_chunk()

    def write_batch(self, records: List[Dict]) -> None:
        """批量写入"""
        for record in records:
            self.write(record)

    def _flush_chunk(self) -> None:
        """将当前 chunk 持久化"""
        if not self._current_chunk:
            return
        self._chunks.append(self._current_chunk)
        self._current_chunk = []

    def flush_to_csv(self, filepath: str, encoding: str = 'utf-8') -> None:
        """将所有已写入的数据刷盘为 CSV 文件"""
        self._flush_chunk()
        self._last_output_path = filepath

        if not self._chunks:
            open(filepath, 'w', encoding=encoding).close()
            return

        headers = list(self._chunks[0][0].keys())
        with open(filepath, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            for chunk in self._chunks:
                for record in chunk:
                    writer.writerow(record)

    def iter_records(self) -> Generator[Dict, None, None]:
        """迭代所有已写入的记录"""
        self._flush_chunk()
        for chunk in self._chunks:
            for record in chunk:
                yield record

    @property
    def total_records(self) -> int:
        """已写入记录总数"""
        return self._total_records

    def cleanup(self) -> None:
        """清理资源"""
        self._chunks.clear()
        self._current_chunk.clear()
        self._total_records = 0
        # 删除已生成的输出文件（若存在）
        if self._last_output_path and os.path.exists(self._last_output_path):
            os.remove(self._last_output_path)
            self._last_output_path = None
