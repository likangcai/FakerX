# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 14:54
# @Software  : PyCharm
# @FileName  : templates.py
# -----------------------------
"""
预设模板系统 - 内置常用数据模型，支持扩展和覆盖
"""

import json
import os
from typing import Dict, Any, Optional
from .exceptions import TemplateNotFoundError

# 内置模板定义
BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "user": {
        "description": "标准用户模型",
        "schema": {
            "id": {"method": "pyint", "min_value": 1, "max_value": 999999},
            "username": {"method": "user_name"},
            "email": {"method": "email"},
            "phone": {"method": "phone_number"},
            "avatar": {"method": "image_url"},
            "created_at": {"method": "date_time_this_year"},
            "status": {
                "elements": ["active", "inactive", "banned"],
                "weights": [0.7, 0.2, 0.1],
            },
        },
    },
    "product": {
        "description": "电商商品模型",
        "schema": {
            "id": {"method": "pyint", "min_value": 1},
            "name": {"method": "catch_phrase"},
            "price": {
                "method": "pyfloat",
                "min_value": 0.01,
                "max_value": 99999.99,
                "right_digits": 2,
            },
            "stock": {"method": "pyint", "min_value": 0, "max_value": 10000},
            "category": {
                "elements": ["电子", "服装", "食品", "家居", "图书"]
            },
            "sku": {"method": "bothify", "text": "???-####"},
            "is_active": {"method": "boolean", "chance_of_getting_true": 85},
        },
    },
    "order": {
        "description": "订单模型",
        "schema": {
            "order_id": {"method": "bothify", "text": "ORD-########"},
            "user_id": {"method": "pyint", "min_value": 1},
            "total_amount": {
                "method": "pyfloat",
                "min_value": 0.01,
                "max_value": 99999.99,
            },
            "status": {
                "elements": ["pending", "paid", "shipped", "delivered", "cancelled"],
                "weights": [0.15, 0.3, 0.2, 0.3, 0.05],
            },
            "created_at": {"method": "date_time_this_year"},
            "payment_method": {
                "elements": ["alipay", "wechat", "credit_card", "bank_transfer"]
            },
        },
    },
    "article": {
        "description": "文章/内容模型",
        "schema": {
            "id": {"method": "pyint", "min_value": 1},
            "title": {"method": "sentence", "nb_words": 6},
            "content": {"method": "paragraph", "nb_sentences": 10},
            "author": {"method": "name"},
            "tags": {
                "method": "random_element",
                "elements": [["tech", "life"], ["news", "hot"], ["tutorial"]],
            },
            "views": {"method": "pyint", "min_value": 0, "max_value": 1000000},
            "published_at": {"method": "date_time_this_year"},
        },
    },
    "log": {
        "description": "日志模型",
        "schema": {
            "timestamp": {"method": "date_time_this_year"},
            "level": {
                "elements": ["DEBUG", "INFO", "WARN", "ERROR"],
                "weights": [0.2, 0.5, 0.2, 0.1],
            },
            "message": {"method": "sentence"},
            "service": {
                "elements": ["api-gateway", "user-service", "order-service",
                             "payment-service"]
            },
            "request_id": {"method": "uuid4"},
        },
    },
}


class TemplateRegistry:
    """模板注册与管理"""

    def __init__(self):
        self._templates: Dict[str, Dict] = {}
        # 加载内置模板
        for name, template in BUILTIN_TEMPLATES.items():
            self._templates[name] = template.copy()

    def get(self, name: str) -> Dict[str, Any]:
        """获取模板"""
        if name not in self._templates:
            available = ", ".join(self._templates.keys())
            raise TemplateNotFoundError(
                f"模板 '{name}' 不存在。可用模板: {available}"
            )
        return self._templates[name]

    def get_schema(
            self,
            name: str,
            extend: Optional[Dict] = None,
            override: Optional[Dict] = None,
    ) -> Dict:
        """
        获取模板 schema，支持扩展和覆盖

        Args:
            name: 模板名称
            extend: 新增字段（不影响原有字段）
            override: 覆盖字段（替换原有字段定义）

        Returns:
            合并后的 schema
        """
        template = self.get(name)
        schema = template["schema"].copy()

        if extend:
            schema.update(extend)

        if override:
            for key, value in override.items():
                if key in schema:
                    schema[key] = value
                else:
                    # override 中包含不存在的字段也添加
                    schema[key] = value

        return schema

    def register(self, name: str, schema: Dict, description: str = ""):
        """注册自定义模板"""
        self._templates[name] = {
            "description": description or f"自定义模板: {name}",
            "schema": schema,
        }

    def load_from_file(self, filepath: str):
        """从 JSON 文件加载模板"""
        with open(filepath, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        if isinstance(templates, dict):
            # 单个模板
            name = templates.get('name', os.path.splitext(filepath)[0])
            self.register(name, templates['schema'], templates.get('description', ''))
        elif isinstance(templates, list):
            # 多个模板
            for tmpl in templates:
                name = tmpl['name']
                self.register(name, tmpl['schema'], tmpl.get('description', ''))

    def load_from_directory(self, dirpath: str):
        """从目录批量加载模板（JSON 文件）"""
        for filename in os.listdir(dirpath):
            if filename.endswith('.json'):
                self.load_from_file(os.path.join(dirpath, filename))

    def list_templates(self) -> Dict[str, str]:
        """列出所有可用模板"""
        return {name: tmpl.get('description', '') for name, tmpl in self._templates.items()}

    def remove(self, name: str):
        """删除模板"""
        if name in BUILTIN_TEMPLATES:
            raise ValueError(f"不能删除内置模板: {name}")
        self._templates.pop(name, None)
