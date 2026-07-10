# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 决策策略基类与统一契约
定义所有具体业务优化决策策略的通用输出模型 StrategyResult 以及抽象基类 BaseStrategy。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from abc import ABC, abstractmethod

@dataclass
class StrategyResult:
    """
    统一的决策策略建议结果模型 (Dataclass)
    """
    strategy_name: str                  # 策略大类名称 (如 "定价优化策略")
    decision_summary: str               # 核心决策一句话摘要 (如 "建议提价至 R$ 85.00")
    suggestions: List[str] = field(default_factory=list) # 具体细分实操建议列表
    confidence_score: float = 1.0       # 决策置信度 (0.0 至 1.0)
    alert_level: str = "green"          # 财务预警级别 ("green" 安全, "yellow" 预警, "red" 危险亏损)
    raw_metrics: Dict[str, Any] = field(default_factory=dict) # 决策支撑数据指标快照


class BaseStrategy(ABC):
    """
    所有决策策略器的抽象基类
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        策略器唯一识别名称
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> StrategyResult:
        """
        执行策略分析逻辑，输出统一的 StrategyResult
        """
        pass
