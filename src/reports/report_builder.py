# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 财务与商业综合报告构建器
负责从商品实物模型 (Product)、销售平台参数 (Platform)、精算指标明细以及一站式运营决策提案 (IntegratedBusinessProposal) 
中提取并格式化拼装出结构化的 BusinessReport DTO 实体。
"""

from src.models.product import Product
from src.models.platform import Platform
from src.models.fee import Fee
from src.calculators.profit_calculator import ProfitResult
from src.strategies.recommendation_strategy import IntegratedBusinessProposal
from src.reports.report_formatter import ReportFormatter
from src.reports.report_models import (
    SummaryReport,
    TaxReport,
    PlatformReport,
    FinancialReport,
    PricingReport,
    MarketingReport,
    InventoryReport,
    WarningReport,
    RecommendationReport,
    BusinessReport
)

class ReportBuilder:
    """
    财务与综合报告生成器 (SOLID - 建造者职责)
    协调格式化器，将离散的、未经格式化的纯数值计算实体和文本提案统一映射至标准 Report 报表领域模型。
    """

    def build_business_report(
        self,
        product: Product,
        platform: Platform,
        proposal: IntegratedBusinessProposal,
        profit_result: ProfitResult,
        tax_fee_brl: float,
        fee_entity: Fee,
        shipping_fee_brl: float,
        tax_regime_name: str = "Simples Nacional",
        effective_tax_rate: float = 0.0
    ) -> BusinessReport:
        """
        全自动化组装 BusinessReport 根容器
        
        Args:
            product: 物理商品 DTO
            platform: 平台销售设定 DTO
            proposal: 一站式综合决策白皮书
            profit_result: 实扣总损益指标
            tax_fee_brl: 纳税金额绝对值 (BRL)
            fee_entity: 平台费扣减实体 (Fee)
            shipping_fee_brl: 卖家实付运费金额 (BRL)
            tax_regime_name: 税制名称描述
            effective_tax_rate: 有效税率比例
            
        Returns:
            BusinessReport: 高级嵌套报表实体 (DTO)
        """
        # 1. 构建概要子报告
        summary_rep = SummaryReport(
            product_sku=product.sku,
            product_name=product.name,
            platform_name=platform.platform_name,
            overall_alert_level=proposal.overall_alert_level,
            generated_at=ReportFormatter.get_sao_paulo_timestamp()
        )

        # 2. 构建税务子报告
        tax_rep = TaxReport(
            tax_regime_name=tax_regime_name,
            total_tax_brl=tax_fee_brl,
            formatted_total_tax=ReportFormatter.brl(tax_fee_brl),
            effective_tax_rate=effective_tax_rate,
            formatted_tax_rate=ReportFormatter.percentage(effective_tax_rate)
        )

        # 3. 构建平台费用子报告
        plat_rep = PlatformReport(
            commission_fee_brl=fee_entity.commission_fee_brl,
            formatted_commission=ReportFormatter.brl(fee_entity.commission_fee_brl),
            fixed_fee_brl=fee_entity.fixed_fee_brl,
            formatted_fixed_fee=ReportFormatter.brl(fee_entity.fixed_fee_brl),
            risk_loss_fee_brl=fee_entity.risk_loss_fee_brl,
            formatted_risk_loss=ReportFormatter.brl(fee_entity.risk_loss_fee_brl),
            total_fee_brl=fee_entity.total_fee_brl,
            formatted_total_fee=ReportFormatter.brl(fee_entity.total_fee_brl)
        )

        # 4. 构建损益核算子报告
        fin_rep = FinancialReport(
            revenue_brl=profit_result.revenue,
            formatted_revenue=ReportFormatter.brl(profit_result.revenue),
            purchase_cost_brl=product.cost_price_brl,
            formatted_purchase_cost=ReportFormatter.brl(product.cost_price_brl),
            total_fee_brl=profit_result.total_fee,
            formatted_total_fee=ReportFormatter.brl(profit_result.total_fee),
            total_tax_brl=profit_result.total_tax,
            formatted_total_tax=ReportFormatter.brl(profit_result.total_tax),
            total_shipping_brl=profit_result.total_shipping,
            formatted_total_shipping=ReportFormatter.brl(profit_result.total_shipping),
            net_profit_brl=profit_result.net_profit,
            formatted_net_profit=ReportFormatter.brl(profit_result.net_profit),
            profit_margin=profit_result.margin,
            formatted_profit_margin=ReportFormatter.percentage(profit_result.margin)
        )

        # 5. 构建定价建议子报告
        pricing_source = proposal.pricing_strategy_report
        metrics_pr = pricing_source.raw_metrics
        pricing_rep = PricingReport(
            breakeven_price_brl=float(metrics_pr["breakeven_price"]),
            formatted_breakeven_price=ReportFormatter.brl(float(metrics_pr["breakeven_price"])),
            target_price_at_15_margin=float(metrics_pr["price_at_15_margin"]),
            formatted_price_at_15_margin=ReportFormatter.brl(float(metrics_pr["price_at_15_margin"])),
            target_price_at_20_margin=float(metrics_pr["price_at_20_margin"]),
            formatted_price_at_20_margin=ReportFormatter.brl(float(metrics_pr["price_at_20_margin"])),
            markdown_budget_brl=float(metrics_pr["breakeven_price"]), # 降价上限参考保本售价差
            formatted_markdown_budget=ReportFormatter.brl(max(platform.selling_price_brl - float(metrics_pr["breakeven_price"]), 0.0))
        )

        # 6. 构建营销推广子报告
        mkt_source = proposal.marketing_strategy_report
        metrics_mk = mkt_source.raw_metrics
        mkt_rep = MarketingReport(
            suggested_ads_budget_ratio=float(metrics_mk["suggested_ad_budget_percentage"]),
            formatted_ads_budget_ratio=ReportFormatter.percentage(float(metrics_mk["suggested_ad_budget_percentage"])),
            suggested_coupon_cap_brl=float(metrics_mk["suggested_coupon_cap"]),
            formatted_coupon_cap=ReportFormatter.brl(float(metrics_mk["suggested_coupon_cap"])),
            marketing_decision_text=mkt_source.decision_summary
        )

        # 7. 构建供应链库存子报告
        inv_source = proposal.supply_chain_strategy_report
        metrics_iv = inv_source.raw_metrics
        inv_rep = InventoryReport(
            recommended_import_channel=inv_source.decision_summary.split("决策：")[-1].replace("】。", "").replace("【", ""),
            replenishment_lead_time_days=int(metrics_iv["lead_time_days"]),
            recommended_moq=int(metrics_iv["moq_suggestion"]),
            recommended_safety_stock=500 if int(metrics_iv["weight_g"]) > 3000 else 50, # 手动基于规则划分
            inventory_decision_text=inv_source.decision_summary
        )

        # 8. 构建财务预警子报告 (抓取 pricing 的状态)
        warn_rep = WarningReport(
            alert_level=proposal.overall_alert_level,
            alert_description=pricing_source.decision_summary,
            warning_list=proposal.combined_suggestions_list[:3] # 汇总前 3 项重点建议作为警告参考
        )

        # 9. 构建综合行动建议子报告
        recom_rep = RecommendationReport(
            primary_platform_recommendation=proposal.primary_platform_recommendation,
            action_items_list=proposal.combined_suggestions_list
        )

        # 10. 组装并返回根
        return BusinessReport(
            summary=summary_rep,
            financial=fin_rep,
            tax=tax_rep,
            platform=plat_rep,
            pricing=pricing_rep,
            marketing=mkt_rep,
            inventory=inv_rep,
            warnings=warn_rep,
            recommendations=recom_rep
        )
