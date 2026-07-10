# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 大模型适配层基类与统一契约
解耦底层不同 LLM API (OpenAI, Gemini, Claude, DeepSeek) 的调用规范。
大模型模块在运行时通过本层向外请求分析，而不直接依赖任何底层 SDK 的具体逻辑。
"""

from typing import Optional, Dict, Any
from src.utils.logger import get_ai_logger

logger = get_ai_logger()

class BaseLLMAdapter:
    """
    所有大语言模型适配器的基类
    """
    @property
    def provider_name(self) -> str:
        """
        返回提供商名称（如 'gemini', 'openai', 'claude', 'deepseek'）
        """
        raise NotImplementedError

    def generate_analysis(self, prompt: str, system_instruction: str = "", temperature: float = 0.2) -> str:
        """
        发送提示词至大模型，并返回其生成的文本结果
        """
        raise NotImplementedError("每一个 LLM 适配器必须实现 generate_analysis 方法")


class AIScoreReport(dict):
    """
    大模型需要返回的标准分析结构模板（AI评估报告的最终产出格式）
    """
    # 注：在业务层可以使用 pydantic 细化，这里做契约规范声明：
    # {
    #     "product_name": "...",            # 商品名称
    #     "market_potential_score": 85,     # 爆款潜力得分 (0-100)
    #     "brazil_trends_fit": "...",       # 巴西市场流行度匹配度及理由
    #     "core_selling_points": ["..."],   # 推荐主打的核心差异化卖点
    #     "competitor_weakness": "...",     # 竞品差评暴露出来的弱点/痛点
    #     "risk_assessment": "...",         # 运营风险评估 (物流是否易碎、退货率高、侵权)
    #     "price_position_suggestion": "..."# 建议售价定价策略
    # }
    pass
