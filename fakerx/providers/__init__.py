"""
FakerX Provider 系统
"""

from .registry import (
    ProviderRegistry,
    register_provider,
    get_provider,
    get_provider_instance,
    list_providers,
    validate_providers,
    _global_registry,
)

__all__ = [
    "ProviderRegistry",
    "register_provider",
    "get_provider",
    "get_provider_instance",
    "list_providers",
    "validate_providers",
    "_global_registry",
]