# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 数据库模块初始化文件
此文件公开数据库核心对象，包括基础模型类 Base、数据库引擎 engine、会话工厂 SessionLocal 及会话生成器 get_db
"""

from src.database.base import Base
from src.database.connection import engine, SessionLocal, get_db

__all__ = ["Base", "engine", "SessionLocal", "get_db"]
