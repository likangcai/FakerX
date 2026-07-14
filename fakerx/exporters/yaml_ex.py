# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:13
# @Software  : PyCharm
# @FileName  : yaml_ex.py
# -----------------------------
"""
YAML 导出器
"""
from typing import List, Dict

from .base import BaseExporter

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class YAMLExporter(BaseExporter):
    """YAML 导出器"""

    def export(self, data: List[Dict], filepath: str, **kwargs):
        if not _YAML_AVAILABLE:
            raise ImportError("YAML 导出需要安装 PyYAML: pip install pyyaml")

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False)

    def export_stream(self, generator, filepath: str, **kwargs):
        if not _YAML_AVAILABLE:
            raise ImportError("YAML 导出需要安装 PyYAML: pip install pyyaml")

        with open(filepath, 'w', encoding='utf-8') as f:
            for record in generator:
                yaml.dump([record], f, allow_unicode=True,
                          default_flow_style=False, sort_keys=False)
