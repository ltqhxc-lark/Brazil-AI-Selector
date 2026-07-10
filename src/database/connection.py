# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - SQLite 数据库连接与会话管理
"""

import os
import yaml
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# 获取项目根目录 (Path 形式，防止路径分隔符在不同系统下出现问题)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 拼接并加载 config/settings.yaml 配置文件
SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"

# 安全加载数据库配置
try:
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # 从配置文件中获取 SQLite 连接串
    DATABASE_URL: str = config["storage"]["database_url"]
except Exception as e:
    # 兜底容错：若加载失败，则默认在项目根目录下的 db 文件夹内创建数据库
    DATABASE_URL = "sqlite:///db/brazil_selector.db"

# 自动处理 SQLite 文件夹创建与绝对路径解析，保证程序从任何工作目录启动都能准确定位数据库文件
if DATABASE_URL.startswith("sqlite:///"):
    # 提取连接串中的相对路径，例如 'db/brazil_selector.db'
    db_rel_path = DATABASE_URL[9:]
    # 解析出完整的项目绝对路径，例如 D:\Brazil-AI-Selector\db\brazil_selector.db
    db_abs_path = (BASE_DIR / db_rel_path).resolve()
    # 自动创建其父目录，确保 db/ 文件夹存在
    db_abs_path.parent.mkdir(parents=True, exist_ok=True)
    # 重新构建绝对路径连接串，避免在不同路径下执行 CLI 时生成多个冗余的 db 文件
    DATABASE_URL = f"sqlite:///{db_abs_path}"

# 创建数据库引擎
# 对于 SQLite，需要设置 check_same_thread=False 允许在多线程（多线程 CLI 或异步后台）中共享会话
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设为 True 可在控制台查看 SQLAlchemy 自动生成的 SQL 语句，开发环境下可手动开启
    connect_args=connect_args
)

# 创建数据库会话工厂 (SessionLocal)
# autocommit=False: 显式开启事务，更改必须手动调用 commit()
# autoflush=False: 避免未显式调用 commit 前自动将状态刷新到数据库
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库 Session 上下文管理器 (生成器模式，支持依赖注入)
    
    Yields:
        Session: SQLAlchemy 数据库会话对象 (Session)
        
    Note:
        在 yield 操作完成后，利用 finally 块确保会话对象一定会被关闭，防止连接和文件锁泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
