# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 14:47
# @Software  : PyCharm
# @FileName  : exceptions.py
# -----------------------------
"""
FakerX 自定义异常类
"""


class FakerXError(Exception):
    """FakerX 基础异常"""
    pass


class SchemaError(FakerXError):
    """Schema 定义错误"""

    def __init__(self, message, path=None):
        self.path = path
        super().__init__(f"[{path}] {message}" if path else message)


class ValidationError(FakerXError):
    """数据验证错误"""
    pass


class TemplateNotFoundError(FakerXError):
    """模板未找到"""
    pass


class ProviderError(FakerXError):
    """Provider 相关错误"""
    pass
