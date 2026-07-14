# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:10
# @Software  : PyCharm
# @FileName  : __init__.py.py
# -----------------------------
"""
导出器模块 - 多格式数据导出
"""

from .base import BaseExporter
from .csv_ex import CSVExporter
from .json_ex import JSONExporter
from .excel_ex import ExcelExporter
from .sql_ex import SQLExporter
from .yaml_ex import YAMLExporter
from .html_ex import HTMLExporter
from .xml_ex import XMLExporter
from .parquet_ex import ParquetExporter

EXPORTERS = {
    'csv': CSVExporter,
    'json': JSONExporter,
    'excel': ExcelExporter,
    'xlsx': ExcelExporter,
    'sql': SQLExporter,
    'yaml': YAMLExporter,
    'yml': YAMLExporter,
    'html': HTMLExporter,
    'htm': HTMLExporter,
    'xml': XMLExporter,
    'parquet': ParquetExporter,
}


def get_exporter(name: str) -> BaseExporter:
    """
    获取指定格式的导出器实例
    :param name: 格式名称（如 'csv', 'json'）或文件扩展名
    :return: BaseExporter 实例
    Raises:
        ValueError: 不支持的格式
    """
    name = name.lower().strip('.')
    exporter_cls = EXPORTERS.get(name)
    if exporter_cls is None:
        supported = ', '.join(EXPORTERS.keys())
        raise ValueError(f"不支持的导出格式: '{name}'。支持的格式: {supported}")
    return exporter_cls()


__all__ = [
    'BaseExporter',
    'CSVExporter',
    'JSONExporter',
    'ExcelExporter',
    'SQLExporter',
    'YAMLExporter',
    'HTMLExporter',
    'XMLExporter',
    'ParquetExporter',
    'get_exporter',
    'EXPORTERS',
]
