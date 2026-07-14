# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : sql_ex.py
# -----------------------------
"""
SQL 导出器
"""

from .base import BaseExporter
from typing import Dict, List, Generator, Any

class SQLExporter(BaseExporter):
    """SQL 导出器 - 生成 SQL INSERT 语句"""

    def export(self, data: List[Dict], filepath: str, table_name: str = 'data',
               **kwargs):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- FakerX Generated SQL Dump\n")
            f.write(f"-- Table: {table_name}\n")
            f.write(f"-- Records: {len(data)}\n\n")

            for record in data:
                flat = self.flatten(record)
                columns = ', '.join(f'"{k}"' for k in flat.keys())
                values = ', '.join(
                    self._format_value(v) for v in flat.values()
                )
                f.write(f'INSERT INTO "{table_name}" ({columns}) VALUES ({values});\n')

    def export_stream(self, generator, filepath: str, table_name: str = 'data',
                      **kwargs):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- FakerX Generated SQL Dump\n")
            f.write(f"-- Table: {table_name}\n\n")

            for record in generator:
                flat = self.flatten(record)
                columns = ', '.join(f'"{k}"' for k in flat.keys())
                values = ', '.join(
                    self._format_value(v) for v in flat.values()
                )
                f.write(f'INSERT INTO "{table_name}" ({columns}) VALUES ({values});\n')

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return 'NULL'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return '1' if value else '0'
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
