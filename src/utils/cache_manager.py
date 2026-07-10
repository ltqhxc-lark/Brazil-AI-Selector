# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 持久化缓存管理器
采用 SQLite 建立键值型本地缓存 (cache/response_cache.db)，有效避免高频重复采集。
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Any
from src.utils.logger import get_crawler_logger

# 获取项目根路径 (D:\Brazil-AI-Selector)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_DB_PATH = os.path.join(CACHE_DIR, "response_cache.db")

logger = get_crawler_logger()

class CacheManager:
    def __init__(self):
        """
        初始化缓存数据库，建立缓存表
        """
        self.conn = sqlite3.connect(CACHE_DB_PATH, check_same_thread=False)
        self._init_table()

    def _init_table(self):
        """
        创建 KV 缓存表，带过期时间
        """
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_value TEXT,
                    expire_at TIMESTAMP
                )
            """)
            # 清理历史已过期的缓存项
            self.conn.execute("DELETE FROM response_cache WHERE expire_at < datetime('now')")

    def get(self, key: str) -> Optional[Any]:
        """
        根据 key 从缓存读取数据。若过期或未命中返回 None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT cache_value, expire_at FROM response_cache WHERE cache_key = ?", (key,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
            
        value_str, expire_str = row
        expire_time = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
        
        if datetime.utcnow() > expire_time:
            # 缓存已过期，执行删除
            self.delete(key)
            logger.info(f"缓存 Key 已过期，清除缓存: {key}")
            return None
            
        logger.info(f"缓存命中，加载本地快照: {key}")
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str

    def set(self, key: str, value: Any, ttl_seconds: int = 86400):
        """
        向缓存写入值，并指定有效时长 (秒)
        """
        try:
            value_str = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            value_str = str(value)
            
        expire_time = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        expire_str = expire_time.strftime("%Y-%m-%d %H:%M:%S")
        
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO response_cache (cache_key, cache_value, expire_at) VALUES (?, ?, ?)",
                (key, value_str, expire_str)
            )
        logger.info(f"缓存存入成功，有效时间: {ttl_seconds}秒, Key: {key}")

    def delete(self, key: str):
        """
        手动清除某一缓存项
        """
        with self.conn:
            self.conn.execute("DELETE FROM response_cache WHERE cache_key = ?", (key,))

    def clear_all(self):
        """
        清空全部缓存
        """
        with self.conn:
            self.conn.execute("DELETE FROM response_cache")
        logger.warning("缓存已全部被排空！")

# 全局单例缓存管理器
cache_manager = CacheManager()
