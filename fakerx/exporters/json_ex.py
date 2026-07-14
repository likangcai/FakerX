# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : json_ex.py
# -----------------------------
"""
JSON 导出器
"""

import json
from datetime import date, datetime, time
from .base import BaseExporter
from typing import List, Dict


class DateTimeEncoder(json.JSONEncoder):
    """处理 datetime/date 等类型的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return super().default(obj)


class JSONExporter(BaseExporter):
    """JSON 导出器"""

    def export(self, data: List[Dict], filepath: str, indent: int = 2,
               encoding: str = 'utf-8', **kwargs):
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=indent,
                      cls=DateTimeEncoder)

    def export_stream(self, generator, filepath: str, encoding: str = 'utf-8', **kwargs):
        with open(filepath, 'w', encoding=encoding) as f:
            for record in generator:
                f.write(json.dumps(record, ensure_ascii=False, cls=DateTimeEncoder) + '\n')

    def to_jsonl(self, data: List[Dict], filepath: str, encoding: str = 'utf-8'):
        with open(filepath, 'w', encoding=encoding) as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False, cls=DateTimeEncoder) + '\n')
