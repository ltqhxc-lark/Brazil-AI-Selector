# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - CSV 二维扁平数据报告物理导出器
"""

import os
import csv
from src.reports.report_models import BusinessReport
from src.exporters.base_exporter import BaseExporter, ExportResult

class CSVExporter(BaseExporter):
    """
    CSV 格式物理文件导出器
    将深度树状的 DTO 扁平化映射为适合 Excel、Pandas 直接读取或快速导入数据库的 Key-Value 结构二维表格。
    """

    def supports(self, format_name: str) -> bool:
        return format_name.lower().strip() == "csv"

    def export(self, report: BusinessReport, output_path: str) -> ExportResult:
        """
        核心物理导出：生成符合国际标准 UTF-8 带 BOM (解决中文在 Excel 中乱码) 的 CSV 表格
        """
        # 1. 安全前置校验
        if not self.validate(report):
            return ExportResult(
                success=False,
                file_path="",
                message="CSV 导出失败：BusinessReport DTO 结构缺失或内容不完整。",
                errors=["BusinessReport instance validation failed."]
            )

        try:
            parent_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(parent_dir, exist_ok=True)

            # 2. 扁平化抽取报表内各个分类的指标项
            rows = [
                ["指标大类", "子项指标", "计算数值 / 运营诊断意见与决策指令"],
                # 概要
                ["Summary (概要)", "Product SKU (商品SKU)", report.summary.product_sku],
                ["Summary (概要)", "Product Name (商品名称)", report.summary.product_name],
                ["Summary (概要)", "Platform (销售平台)", report.summary.platform_name],
                ["Summary (概要)", "Alert Level (预警评级)", report.summary.overall_alert_level.upper()],
                ["Summary (概要)", "Generated At (时区戳)", report.summary.generated_at],
                # 财务损益
                ["Financial (财务损益)", "Revenue (预计营收)", report.financial.formatted_revenue],
                ["Financial (财务损益)", "Purchase Cost (采购成本)", report.financial.formatted_purchase_cost],
                ["Financial (财务损益)", "Total Platform Fee (平台费合计)", report.financial.formatted_total_fee],
                ["Financial (财务损益)", "Total Taxes (税收合计)", report.financial.formatted_total_tax],
                ["Financial (财务损益)", "Total Shipping (卖家付运费)", report.financial.formatted_total_shipping],
                ["Financial (财务损益)", "Net Profit (预计纯利润)", report.financial.formatted_net_profit],
                ["Financial (财务损益)", "Profit Margin (纯利润率)", report.financial.formatted_profit_margin],
                # 定价建议
                ["Pricing (价格调校)", "Breakeven Price (保本价格底线)", report.pricing.formatted_breakeven_price],
                ["Pricing (价格调校)", "Suggested Price at 15% Margin (15%黄金售价)", report.pricing.formatted_price_at_15_margin],
                ["Pricing (价格调校)", "Suggested Price at 20% Margin (20%金牌售价)", report.pricing.formatted_price_at_20_margin],
                ["Pricing (价格调校)", "Max Markdown Budget (黑五最大促销降价限额)", report.pricing.formatted_markdown_budget],
                # 营销广告
                ["Marketing (广告投放)", "PPC Ads Ratio Suggestion (建议CPC广告费占比)", report.marketing.formatted_ads_budget_ratio],
                ["Marketing (广告投放)", "Max Coupon Cap (优惠券最大券额限制)", report.marketing.formatted_coupon_cap],
                ["Marketing (广告投放)", "Operational Marketing Proposal (营销综合打法)", report.marketing.marketing_decision_text],
                # 供应链备货
                ["Inventory (供应链控制)", "Recommended Clearance Channel (推荐通关模式)", report.inventory.recommended_import_channel],
                ["Inventory (供应链控制)", "Lead Time (补货物流提前期)", f"{report.inventory.replenishment_lead_time_days} 天"],
                ["Inventory (供应链控制)", "Recommended MOQ (建议起订量)", f"{report.inventory.recommended_moq} 件"],
                ["Inventory (供应链控制)", "Recommended Safety Stock (常备安全库存)", f"{report.inventory.recommended_safety_stock} 件"],
                ["Inventory (供应链控制)", "Replenishment Strategy (备货控制细节)", report.inventory.inventory_decision_text]
            ]

            # 3. 汇总行动指令
            for idx, action in enumerate(report.recommendations.action_items_list, 1):
                rows.append(["Action Items (行动清单)", f"Action Step {idx} (第 {idx} 步操作)", action])

            # 4. 磁盘写入：使用 'utf-8-sig' 格式写入。
            # 这是中国本地和 Windows Excel 最完美的 CSV 格式，能够强制 Excel 在双击打开时以 UTF-8 解码，绝不出现任何乱码。
            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            return ExportResult(
                success=True,
                file_path=os.path.abspath(output_path),
                message=f"成功将财务分析报告扁平二维化并导出为 CSV 文件！物理路径: {output_path}"
            )
        except Exception as e:
            return ExportResult(
                success=False,
                file_path="",
                message=f"CSV 导出运行异常: {str(e)}",
                errors=[f"File I/O or csv write error: {str(e)}"]
            )
