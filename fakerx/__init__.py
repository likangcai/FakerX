"""
FakerX - Enhanced Fake Data Generation Library

一个基于 Faker 的增强版测试数据生成库，支持：
- 结构化 Schema 生成（字段引用、条件逻辑、跨表关联）
- 预设模板系统
- 数据脱敏
- 流式生成与导出
- Schema 验证
- 自定义 Provider 注册
"""

from .fakerx import FakerX
from .schema import SchemaGenerator
from .validators import SchemaValidator,SchemaValidatorEnhanced
from .anonymizer import DataAnonymizer
from .templates import TemplateRegistry, BUILTIN_TEMPLATES
from .exporters import CSVExporter, JSONExporter, get_exporter as _get_exporter
from .exceptions import (
    FakerXError, SchemaError, ValidationError,
    TemplateNotFoundError, ProviderError,
)

__version__ = "2.0.0"
__all__ = [
    "FakerX",
    "SchemaGenerator",
    "SchemaValidator",
    "SchemaValidatorEnhanced",
    "DataAnonymizer",
    "TemplateRegistry",
    "BUILTIN_TEMPLATES",
    "CSVExporter",
    "JSONExporter",
    "FakerXError",
    "SchemaError",
    "ValidationError",
    "TemplateNotFoundError",
    "ProviderError",
]
