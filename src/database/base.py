# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - SQLAlchemy 2.0 声明性基类
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 声明性模型基类
    本项目的所有实体模型 (Models) 都必须继承自该基类以接入 ORM 映射
    """
    pass
