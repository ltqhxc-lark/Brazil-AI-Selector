# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 报告本地化显示格式化工具
整合系统基础 Utils 格式化器，提供报告专用的圣保罗时区时间戳戳记和高阶字符拼装。
"""

from datetime import datetime, timedelta, timezone
from src.utils.formatter import format_brl, format_usd, format_percentage, format_weight

class ReportFormatter:
    """
    报告特定数据格式化器 (SOLID - 格式化职责)
    管理报告 DTO 在组装过程中所要求的货币、比例、质量、以及特定巴西本地时间的转换呈现。
    """

    @staticmethod
    def brl(value: float) -> str:
        """
        转换为巴西雷亚尔本地货帀 R$ 样式
        """
        return format_brl(value)

    @staticmethod
    def usd(value: float) -> str:
        """
        转换为美元标示样式
        """
        return format_usd(value)

    @staticmethod
    def percentage(value: float, decimals: int = 2) -> str:
        """
        转换为百分比样式 (如 "12.50%")
        """
        return format_percentage(value, decimals)

    @staticmethod
    def weight(weight_g: float) -> str:
        """
        转换为易读的重量样式 (如 "1.25 kg")
        """
        return format_weight(weight_g)

    @staticmethod
    def get_sao_paulo_timestamp() -> str:
        """
        获取巴西圣保罗 (America/Sao_Paulo) 本地当前的格式化时间戳字符串 (BRT)
        
        Note:
            优先使用 zoneinfo 获取标准时区，若系统环境缺失则降级使用手动固定的 UTC-3 偏移量，
            保证程序在任何海外 Docker 容器或 Windows 系统下运行结果绝对正确。
        """
        try:
            from zoneinfo import ZoneInfo
            sp_time = datetime.now(ZoneInfo("America/Sao_Paulo"))
        except Exception:
            # 巴西目前已取消夏令时，常年处于西三区 (UTC-3)
            sp_tz = timezone(timedelta(hours=-3))
            sp_time = datetime.now(sp_tz)
            
        return sp_time.strftime("%Y-%m-%d %H:%M:%S BRT")
