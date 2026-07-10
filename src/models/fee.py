# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 费用明细数据模型
"""

from dataclasses import dataclass

@dataclass
class Fee:
    """
    费用明细数据模型 (纯内存数据结构)
    用于统一存储计算引擎输出的各项扣点、运费、税费及准备金明细。
    各计算器将填充该对象，以便业务汇总和利润看板的完美展示。
    """
    commission_fee_brl: float     # 平台收取的比例销售佣金 (单位: BRL 雷亚尔)
    fixed_fee_brl: float          # 平台收取的单笔/单件固定成交手续费 (单位: BRL 雷亚尔)
    shipping_fee_brl: float       # 卖家实际支付/承担的物流运费 (单位: BRL 雷亚尔)
    tax_fee_brl: float            # 本次销售应缴纳的各种流转税、统一税或进口关税总额 (单位: BRL 雷亚尔)
    affiliate_fee_brl: float      # 给网络达人或分销联盟的分账佣金 (单位: BRL 雷亚尔)
    risk_loss_fee_brl: float      # 针对货损、丢包、恶意退单等预留的风险损失准备金 (单位: BRL 雷亚尔)
    other_fee_brl: float = 0.0    # 运营中产生的其他额外杂费 (单位: BRL 雷亚尔，默认 0.0)
    total_fee_brl: float = 0.0    # 汇总的总运营相关费用扣减 (单位: BRL 雷亚尔，等于以上各项的累加值)
