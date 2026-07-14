# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : csv_ex.py
# -----------------------------
"""
CSV 导出器
"""

import csv
from .base import BaseExporter
from typing import Dict, List, Optional


class CSVExporter(BaseExporter):
    """CSV 导出器"""

    def export(self, data: List[Dict], filepath: str, encoding: str = 'utf-8',
               headers: Optional[List[str]] = None, **kwargs):
        if not data:
            return
        flat_data = [self.flatten(row) for row in data]
        actual_headers = headers or list(flat_data[0].keys())
        with open(filepath, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=actual_headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(flat_data)

    def export_stream(self, generator, filepath: str, encoding: str = 'utf-8',
                      headers: Optional[List[str]] = None, **kwargs):
        with open(filepath, 'w', newline='', encoding=encoding) as f:
            writer = None
            for record in generator:
                flat = self.flatten(record)
                if writer is None:
                    actual_headers = headers or list(flat.keys())
                    writer = csv.DictWriter(f, fieldnames=actual_headers, extrasaction='ignore')
                    writer.writeheader()
                writer.writerow(flat)
