# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台插件注册表 (Registry)
提供灵活的装饰器注册机制，支持动态载入、热拔插，为未来无缝添加 Amazon, Magalu 等平台做基础设计
"""

import os
import importlib
from typing import Dict, Type
from src.platforms.base_platform import BasePlatformPlugin
from src.utils.logger import get_crawler_logger

logger = get_crawler_logger()

class PlatformRegistry:
    # 存储注册的平台插件实例，格式：{ 'platform_name': PluginInstance }
    _registry: Dict[str, BasePlatformPlugin] = {}

    @classmethod
    def register(cls, name: str):
        """
        注册平台插件的类装饰器
        使用方式：
        @PlatformRegistry.register("shopee")
        class ShopeePlugin(BasePlatformPlugin):
            ...
        """
        def decorator(subclass: Type[BasePlatformPlugin]):
            instance = subclass()
            cls._registry[name] = instance
            logger.info(f"成功注册平台插件: [{name}] - 类名: {subclass.__name__}")
            return subclass
        return decorator

    @classmethod
    def get_plugin(cls, name: str) -> BasePlatformPlugin:
        """
        获取指定平台插件的实例
        """
        plugin = cls._registry.get(name)
        if not plugin:
            # 尝试动态加载内置或第三方插件
            logger.warning(f"平台插件 [{name}] 未在注册表中，尝试进行动态导入加载...")
            cls._auto_import_plugin(name)
            plugin = cls._registry.get(name)
            
        if not plugin:
            raise KeyError(f"未找到名为 '{name}' 的已注册平台。请确保它被声明在 'src/platforms' 或其 plugins 目录下并正确使用了 @PlatformRegistry.register 装饰器。")
        return plugin

    @classmethod
    def list_registered_platforms(cls) -> list:
        """
        列出当前系统中已经就绪可用的全部平台
        """
        return list(cls._registry.keys())

    @classmethod
    def _auto_import_plugin(cls, name: str):
        """
        如果请求的平台尚未注册，动态从 src/platforms 目录或 src/platforms/plugins 目录进行搜索加载
        """
        try:
            # 尝试导入同名的内置文件
            importlib.import_module(f"src.platforms.{name}")
            logger.info(f"成功通过动态导入加载了内置平台文件: src.platforms.{name}")
        except ModuleNotFoundError:
            try:
                # 尝试导入 plugins 下的扩展文件
                importlib.import_module(f"src.platforms.plugins.{name}")
                logger.info(f"成功通过动态导入加载了扩展平台插件: src.platforms.plugins.{name}")
            except ModuleNotFoundError:
                logger.error(f"动态导入平台文件失败，未在本地磁盘找到关联的模块: {name}")
