# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2026/7/14 15:12
# @Software  : PyCharm
# @FileName  : registry.py
# -----------------------------
"""
Provider 注册中心 - 管理 FakerX 的自定义 Provider
"""

from typing import Dict, Type, Any, Optional, List
from faker.providers import BaseProvider
from ..exceptions import ProviderError


class ProviderRegistry:
    """
    Provider 注册中心

    管理所有自定义 Provider，支持:
    - 注册单个 Provider
    - 批量注册
    - 查找 Provider
    - Provider 依赖管理
    """

    def __init__(self):
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._provider_instances: Dict[str, BaseProvider] = {}
        self._dependencies: Dict[str, List[str]] = {}

    def register(self, name: str, provider_class: Type[BaseProvider],
                 dependencies: Optional[List[str]] = None):
        """
        注册 Provider
        :param name: Provider 名称
        :param provider_class: Provider 类
        :param dependencies: 依赖的其他 Provider 名称列表
        :return:
        """

        if not issubclass(provider_class, BaseProvider):
            raise ProviderError(
                f"Provider 类必须继承自 BaseProvider: {provider_class}"
            )

        self._providers[name] = provider_class
        if dependencies:
            self._dependencies[name] = dependencies

    def register_instance(self, name: str, provider_instance: BaseProvider):
        """注册 Provider 实例"""
        if not isinstance(provider_instance, BaseProvider):
            raise ProviderError(
                f"Provider 实例必须继承自 BaseProvider: {provider_instance}"
            )
        self._provider_instances[name] = provider_instance

    def get_provider(self, name: str) -> Type[BaseProvider]:
        """获取 Provider 类"""
        if name not in self._providers:
            raise ProviderError(f"未注册的 Provider: {name}")
        return self._providers[name]

    def get_provider_instance(self, name: str) -> BaseProvider:
        """获取 Provider 实例"""
        if name in self._provider_instances:
            return self._provider_instances[name]

        provider_class = self.get_provider(name)
        instance = provider_class(self._get_generator())
        self._provider_instances[name] = instance
        return instance

    @staticmethod
    def _get_generator():
        """获取 Faker 生成器实例"""
        from faker import Faker
        return Faker()

    def has_provider(self, name: str) -> bool:
        """检查 Provider 是否已注册"""
        return name in self._providers

    def list_providers(self) -> List[str]:
        """列出所有已注册的 Provider"""
        return list(self._providers.keys())

    def resolve_dependencies(self, name: str) -> List[str]:
        """解析 Provider 的依赖链"""
        if name not in self._dependencies:
            return []

        dependencies = self._dependencies[name]
        resolved = set(dependencies)

        # 递归解析依赖
        for dep in dependencies:
            if dep in self._dependencies:
                resolved.update(self.resolve_dependencies(dep))

        return list(resolved)

    def validate_dependencies(self):
        """验证所有 Provider 的依赖是否完整"""
        errors = []
        for name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._providers:
                    errors.append(f"Provider '{name}' 依赖未注册的 Provider: '{dep}'")

        if errors:
            raise ProviderError(
                "Provider 依赖验证失败:\n" + "\n".join(errors)
            )

    def clear(self):
        """清空所有注册"""
        self._providers.clear()
        self._provider_instances.clear()
        self._dependencies.clear()


# 全局注册中心实例
_global_registry = ProviderRegistry()


def register_provider(name: str, provider_class: Type[BaseProvider],
                      dependencies: Optional[List[str]] = None):
    """全局注册 Provider"""
    _global_registry.register(name, provider_class, dependencies)


def get_provider(name: str) -> Type[BaseProvider]:
    """全局获取 Provider 类"""
    return _global_registry.get_provider(name)


def get_provider_instance(name: str) -> BaseProvider:
    """全局获取 Provider 实例"""
    return _global_registry.get_provider_instance(name)


def list_providers() -> List[str]:
    """全局列出所有 Provider"""
    return _global_registry.list_providers()


def validate_providers():
    """全局验证 Provider 依赖"""
    _global_registry.validate_dependencies()
