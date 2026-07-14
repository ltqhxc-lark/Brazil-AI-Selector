import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine
from alembic import context

# 1. 动态加载项目根目录，支持 CLI 从任何工作目录启动
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 导入项目配置及数据库连接以进行动态 URL 解析
from src.database.connection import DATABASE_URL
from src.database.base import Base
# 导入选品模块模型以加载 metadata 进入 Base 实例
from src.product_selection.db_models import SelectionProductDB, SelectionMarketDataDB, SelectionResultDB

# Alembic 配置文件对象
config = context.config

# 如果存在配置文件，设置日志解析器
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置打分与试算模型元数据
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    在离线模式下运行迁移。
    只需动态设置会话连接 URL，不依赖数据库驱动连接实例。
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式下运行迁移（包含实际数据库建立与升级连接）。
    """
    # 动态创建连接引擎，避免在 alembic.ini 中硬编码路径
    connectable = create_engine(DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
