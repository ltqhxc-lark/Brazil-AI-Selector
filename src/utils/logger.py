# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 多文件日志系统
实现对不同模块日志的高级隔离，分别记录到各自的目标日志文件中：
- error.log: 严重错误及未捕获异常
- crawler.log: 采集与网页爬虫状态
- profit.log: 财务与税率计算详情
- ai.log: 大模型调用、Tokens消耗与评估分析
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# 获取项目根路径 (D:\Brazil-AI-Selector)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 自动建立 logs/ 文件夹
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def create_rotating_handler(filename: str, level: int) -> RotatingFileHandler:
    """
    创建带自动轮转的日志处理器，防单个日志文件过大 (限5MB，保留5个备份)
    """
    filepath = os.path.join(LOG_DIR, filename)
    handler = RotatingFileHandler(filepath, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler

def setup_loggers():
    """
    全局日志系统配置初始化
    """
    # 避免重复初始化
    if logging.getLogger("crawler").hasHandlers():
        return

    # 1. 采集模块专用 Logger -> crawler.log
    crawler_logger = logging.getLogger("crawler")
    crawler_logger.setLevel(logging.INFO)
    crawler_logger.addHandler(create_rotating_handler("crawler.log", logging.INFO))
    crawler_logger.propagate = False  # 防止向父 logger 渗透导致打印重复

    # 2. 财务精算专用 Logger -> profit.log
    profit_logger = logging.getLogger("profit")
    profit_logger.setLevel(logging.INFO)
    profit_logger.addHandler(create_rotating_handler("profit.log", logging.INFO))
    profit_logger.propagate = False

    # 3. AI 模块专用 Logger -> ai.log
    ai_logger = logging.getLogger("ai")
    ai_logger.setLevel(logging.INFO)
    ai_logger.addHandler(create_rotating_handler("ai.log", logging.INFO))
    ai_logger.propagate = False

    # 4. 全局系统根 Logger (兼顾记录所有 ERROR 级别日志 -> error.log)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(create_rotating_handler("error.log", logging.ERROR))

    # 如果是开发环境，添加控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)

# 自动执行初始化
setup_loggers()

# 暴露获取各 logger 的接口，方便外部导入
def get_crawler_logger() -> logging.Logger:
    return logging.getLogger("crawler")

def get_profit_logger() -> logging.Logger:
    return logging.getLogger("profit")

def get_ai_logger() -> logging.Logger:
    return logging.getLogger("ai")

def get_system_logger() -> logging.Logger:
    return logging.getLogger()
