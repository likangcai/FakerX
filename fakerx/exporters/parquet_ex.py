# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : parquet_ex.py
# -----------------------------
"""
Parquet 导出器
"""
from typing import List, Dict

from .base import BaseExporter

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    _PARQUET_AVAILABLE = True
except ImportError:
    _PARQUET_AVAILABLE = False


class ParquetExporter(BaseExporter):
    """Parquet 导出器"""

    def export(self, data: List[Dict], filepath: str, **kwargs):
        if not _PARQUET_AVAILABLE:
            raise ImportError("Parquet 导出需要安装 pyarrow: pip install pyarrow")

        if not data:
            return

        flat_data = [self.flatten(row) for row in data]
        table = pa.Table.from_pylist(flat_data)
        pq.write_table(table, filepath)

    def export_stream(self, generator, filepath: str, chunk_size: int = 10000,
                      **kwargs):
        if not _PARQUET_AVAILABLE:
            raise ImportError("Parquet 导出需要安装 pyarrow: pip install pyarrow")

        writer = None
        chunk = []

        for record in generator:
            chunk.append(self.flatten(record))
            if len(chunk) >= chunk_size:
                table = pa.Table.from_pylist(chunk)
                if writer is None:
                    writer = pq.ParquetWriter(filepath, table.schema)
                writer.write_table(table)
                chunk = []

        if chunk:
            table = pa.Table.from_pylist(chunk)
            if writer is None:
                pq.write_table(table, filepath)
            else:
                writer.write_table(table)

        if writer:
            writer.close()
