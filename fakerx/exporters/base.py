# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:12
# @Software  : PyCharm
# @FileName  : base.py
# -----------------------------
"""
导出器基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Generator, Any
import json


class BaseExporter(ABC):
    """
    导出器基类
    """

    @abstractmethod
    def export(self, data: List[Dict], filepath: str, **kwargs):
        """导出列表数据"""
        pass

    @abstractmethod
    def export_stream(self, generator: Generator[Dict, None, None], filepath: str, **kwargs):
        """流式导出"""
        pass

    @staticmethod
    def flatten(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """展平嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(BaseExporter.flatten(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v, ensure_ascii=False)))
            else:
                items.append((new_key, v))
        return dict(items)
