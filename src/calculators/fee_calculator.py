# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 平台费用精算器
根据各个平台的规则及卖家设定的销售参数，精算销售佣金、固定手续费、免邮费率（FSS）、达人佣金、损耗准备金等各项杂费。
"""

import yaml
from pathlib import Path
from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.utils.money import add_money, multiply_money, calculate_percentage, round_to_two

# 定位项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def load_settings() -> dict:
    """
    加载全局 settings.yaml 配置文件
    """
    settings_path = BASE_DIR / "config" / "settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_platform_rules() -> dict:
    """
    加载 platform_rules.yaml 配置文件
    """
    settings = load_settings()
    rules_path = BASE_DIR / settings["config_files"]["platform_rules_path"]
    with open(rules_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_taxes_config() -> dict:
    """
    加载 taxes_brazil.yaml 配置文件
    """
    settings = load_settings()
    taxes_path = BASE_DIR / settings["config_files"]["taxes_config_path"]
    with open(taxes_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class FeeCalculator:
    """
    平台费用计算器 (SOLID - 单一职责)
    负责针对三大平台在巴西本土运营产生的各项成交手续费、抽点和风险计提。
    """

    def __init__(self) -> None:
        # 在初始化时一次性安全加载平台费率配置
        self.rules = load_platform_rules()

    def calculate(self, product: Product, platform: Platform) -> Fee:
        """
        计算单笔交易所产生的全部平台相关费用明细
        
        Args:
            product: 商品数据模型 (Product)
            platform: 平台销售参数数据模型 (Platform)
            
        Returns:
            Fee: 填充了所有费用分解明细的数据模型
        """
        pid = platform.platform_id.lower().strip()
        
        if pid == "mercado_livre_brasil":
            return self._calculate_mercado_livre(product, platform)
        elif pid == "shopee_brasil":
            return self._calculate_shopee(product, platform)
        elif pid == "tiktok_shop_brasil":
            return self._calculate_tiktok(product, platform)
        else:
            # 容错返回空费用
            return Fee(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def _calculate_mercado_livre(self, product: Product, platform: Platform) -> Fee:
        """
        美客多巴西平台费用精算
        """
        cfg = self.rules["mercado_livre_brasil"]
        price = platform.selling_price_brl

        # 1. 销售佣金率匹配 (经典 Classic 与 黄金 Premium 档次)
        # 铂金/黄金/绿标卖家默认跑 Premium 黄金曝光，普通卖家默认 Classic 经典曝光
        is_premium_listing = platform.seller_level in ("platinum", "gold", "leader")
        comm_rates = cfg["commission_rates"]
        rate = comm_rates["premium"] if is_premium_listing else comm_rates["classic"]
        commission_fee = calculate_percentage(price, rate)

        # 2. 低价商品固定销售手续费 (Tarifa Fixa)
        # 低于 79.00 BRL 加收 6.00 BRL 手续费
        fixed_cfg = cfg["fixed_fee"]
        fixed_fee = float(fixed_cfg["fee_brl"]) if price < fixed_cfg["threshold_brl"] else 0.0

        # 3. 风险计提损耗准备金 (退货、丢包率)
        risk_cfg = cfg["risk_factors"]
        total_risk_rate = risk_cfg["return_rate"] + risk_cfg["loss_rate"]
        risk_loss_fee = calculate_percentage(price, total_risk_rate)

        # 汇总
        total_fee = round_to_two(commission_fee + fixed_fee + risk_loss_fee)

        return Fee(
            commission_fee_brl=commission_fee,
            fixed_fee_brl=fixed_fee,
            shipping_fee_brl=0.0,       # 运费不在此处计算，由 shipping_calculator 统一核算
            tax_fee_brl=0.0,            # 税费由 tax_calculator 统一核算
            affiliate_fee_brl=0.0,       # 美客多不收取默认分销比例费 (联盟营销暂计0)
            risk_loss_fee_brl=risk_loss_fee,
            other_fee_brl=0.0,
            total_fee_brl=total_fee
        )

    def _calculate_shopee(self, product: Product, platform: Platform) -> Fee:
        """
        虾皮巴西平台费用精算
        """
        cfg = self.rules["shopee_brasil"]
        price = platform.selling_price_brl
        comm_cfg = cfg["commission"]

        # 1. 基础佣金与支付交易费：基础 14% + 2% 支付手续费
        base_comm_fee = calculate_percentage(price, comm_cfg["base_rate"])
        payment_fee = calculate_percentage(price, comm_cfg["payment_processing_rate"])
        commission_fee = round_to_two(base_comm_fee + payment_fee)

        # 2. 免邮计划 (FSS) 额外抽佣 (6%，单件封顶 R$ 30)
        fss_fee = 0.0
        if platform.participate_fss:
            fss_cfg = comm_cfg["free_shipping_program"]
            raw_fss = calculate_percentage(price, fss_cfg["extra_rate"])
            fss_fee = min(raw_fss, float(fss_cfg["max_extra_fee_cap_brl"]))

        # 3. 单件固定交易手续费 (2026最新政策 R$ 3.00)
        fixed_fee = float(comm_cfg["fixed_fee_per_item_brl"])

        # 4. 风险计提损耗准备金 (默认 2%)
        risk_rate = float(cfg["shipping"]["loss_and_return_rate"])
        risk_loss_fee = calculate_percentage(price, risk_rate)

        # 汇总
        total_fee = round_to_two(commission_fee + fss_fee + fixed_fee + risk_loss_fee)

        return Fee(
            commission_fee_brl=commission_fee,
            fixed_fee_brl=fixed_fee,
            shipping_fee_brl=0.0,
            tax_fee_brl=0.0,
            affiliate_fee_brl=fss_fee,   # 将免邮服务费 (FSS) 作为增值流量包归类
            risk_loss_fee_brl=risk_loss_fee,
            other_fee_brl=0.0,
            total_fee_brl=total_fee
        )

    def _calculate_tiktok(self, product: Product, platform: Platform) -> Fee:
        """
        TikTok Shop 巴西平台费用精算
        """
        cfg = self.rules["tiktok_shop_brasil"]
        price = platform.selling_price_brl
        comm_cfg = cfg["commission"]

        # 1. 基础销售佣金率 (15%) 或 新卖家促销价 (1.99%)
        incentive = comm_cfg["new_seller_incentive"]
        rate = comm_cfg["base_rate"]
        if incentive["enabled"]:
            rate = incentive["promo_rate"]
        commission_fee = calculate_percentage(price, rate)

        # 2. 单笔订单固定收取处理费 (R$ 1.00)
        fixed_fee = float(comm_cfg["fixed_handling_fee_brl"])

        # 3. 达人联盟营销佣金 (TikTok 特有分销佣金)
        affiliate_fee = 0.0
        if comm_cfg["affiliate"]["enabled"] and platform.affiliate_rate > 0:
            # 校验达人分销比率
            aff_rate = max(platform.affiliate_rate, float(comm_cfg["affiliate"]["min_rate"]))
            affiliate_fee = calculate_percentage(price, aff_rate)

        # 4. 风险计提损耗准备金 (默认 1.5%)
        risk_rate = float(cfg["shipping"]["loss_and_return_rate"])
        risk_loss_fee = calculate_percentage(price, risk_rate)

        # 汇总
        total_fee = round_to_two(commission_fee + fixed_fee + affiliate_fee + risk_loss_fee)

        return Fee(
            commission_fee_brl=commission_fee,
            fixed_fee_brl=fixed_fee,
            shipping_fee_brl=0.0,
            tax_fee_brl=0.0,
            affiliate_fee_brl=affiliate_fee,
            risk_loss_fee_brl=risk_loss_fee,
            other_fee_brl=0.0,
            total_fee_brl=total_fee
        )
