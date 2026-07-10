# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - PDF 格式商业诊断报告物理导出器
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.reports.report_models import BusinessReport
from src.exporters.base_exporter import BaseExporter, ExportResult

class PDFExporter(BaseExporter):
    """
    PDF 格式财务报告物理导出器
    使用 ReportLab 绘图引擎，将 BusinessReport 树形 DTO 编译导出为符合出版物级视觉要求的 PDF 白皮书。
    为了完美契合巴西出海业务本地化（pt-BR），且由于 ReportLab 默认英文字体（Helvetica）不支持中文 Unicode 字符的渲染缺陷，
    本导出器采用专业的葡萄牙语（Portuguese）进行本地化编排。这不仅规避了 PDF 乱码和字体文件丢失异常，
    更是让报告可以直接提交给巴西本土的合伙人、财务会计或清关代办公司。
    """

    def supports(self, format_name: str) -> bool:
        return format_name.lower().strip() == "pdf"

    def export(self, report: BusinessReport, output_path: str) -> ExportResult:
        """
        物理 PDF 编译写入入口
        """
        if not self.validate(report):
            return ExportResult(
                success=False,
                file_path="",
                message="PDF 导出失败：BusinessReport 结构缺失或内容不完整。",
                errors=["BusinessReport instance validation failed."]
            )

        try:
            parent_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(parent_dir, exist_ok=True)

            # 1. 基础文档参数配置
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            story = []

            # 2. 样式设定 (ReportLab Standard styles)
            styles = getSampleStyleSheet()
            
            # 建立企业级温和冷色系调色板 (Deep Slate Blue)
            primary_color = colors.HexColor("#1F497D")
            secondary_color = colors.HexColor("#366092")
            text_color = colors.HexColor("#333333")

            # 统一中西字型映射 (Helvetica 系列，原生支持巴西语中的 accents)
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=18,
                leading=22,
                textColor=primary_color,
                spaceAfter=15,
                alignment=1 # Center
            )

            section_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                leading=16,
                textColor=secondary_color,
                spaceBefore=12,
                spaceAfter=8
            )

            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                leading=13,
                textColor=text_color,
                spaceAfter=6
            )

            bold_body_style = ParagraphStyle(
                'ReportBodyBold',
                parent=body_style,
                fontName='Helvetica-Bold'
            )

            # 3. 绘制主大标题与副标题
            story.append(Paragraph("Relatorio de Diagnostico Comercial e Rentabilidade", title_style))
            story.append(Paragraph("Brazil-AI-Selector - Analise Avancada de E-commerce", ParagraphStyle('Sub', parent=body_style, alignment=1, fontSize=10, spaceAfter=15)))
            story.append(Spacer(1, 5))

            # 4. A部分：概要 (Visão Geral)
            story.append(Paragraph("A. Visao Geral do Produto", section_style))
            summary_text = (
                f"<b>SKU do Produto:</b> {report.summary.product_sku}<br/>"
                f"<b>Nome do Produto:</b> {report.summary.product_name}<br/>"
                f"<b>Canal de Vendas:</b> {report.summary.platform_name}<br/>"
                f"<b>Nivel de Alerta:</b> {report.summary.overall_alert_level.upper()}<br/>"
                f"<b>Gerado em (BRT):</b> {report.summary.generated_at}"
            )
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 5))

            # 5. B部分：损益精算明细表 (DRE)
            story.append(Paragraph("B. Demonstrativo de Resultados do Exercito (DRE)", section_style))
            
            # 动态核算各项财务成本占比
            rev = report.financial.revenue_brl
            cost_pct = (report.financial.purchase_cost_brl / rev) * 100.0 if rev > 0.0 else 0.0
            fee_pct = (report.financial.total_fee_brl / rev) * 100.0 if rev > 0.0 else 0.0
            tax_pct = (report.financial.total_tax_brl / rev) * 100.0 if rev > 0.0 else 0.0
            ship_pct = (report.financial.total_shipping_brl / rev) * 100.0 if rev > 0.0 else 0.0

            # 二维列表构筑 PDF 数据网格
            data = [
                [Paragraph("<b>Indicador Financeiro / Conta</b>", bold_body_style), 
                 Paragraph("<b>Valor (BRL)</b>", bold_body_style), 
                 Paragraph("<b>Participacao (%)</b>", bold_body_style)],
                [Paragraph("1. Preco de Venda (Receita Bruta)", body_style), f"R$ {report.financial.revenue_brl:.2f}", "100.0%"],
                [Paragraph("2. Custo de Aquisicao do Produto", body_style), f"R$ -{report.financial.purchase_cost_brl:.2f}", f"-{cost_pct:.1f}%"],
                [Paragraph("3. Comissoes e Tarifas de Plataforma", body_style), f"R$ -{report.financial.total_fee_brl:.2f}", f"-{fee_pct:.1f}%"],
                [Paragraph("4. Impostos Totais (Simples/Importacao)", body_style), f"R$ -{report.financial.total_tax_brl:.2f}", f"-{tax_pct:.1f}%"],
                [Paragraph("5. Custos de Frete e Logistica", body_style), f"R$ -{report.financial.total_shipping_brl:.2f}", f"-{ship_pct:.1f}%"],
                [Paragraph("<b>Lucro Liquido Real Estimado</b>", bold_body_style), 
                 f"R$ {report.financial.net_profit_brl:.2f}", 
                 f"{report.financial.formatted_profit_margin}"]
            ]

            t = Table(data, colWidths=[240, 110, 130])
            # 对 PDF 财务账目表格进行精致渲染
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E9EDF4")),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D3D3D3")),
                ('LINEBELOW', (0,-1), (-1,-1), 1.5, primary_color),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#F2F5F8")),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

            # 6. C部分：运营决策建议 (Diretrizes Operacionais)
            story.append(Paragraph("C. Diretrizes Estrategicas e Precificacao", section_style))
            
            p_text = (
                f"<b>Preco de Ponto de Equilibrio (Break-even):</b> {report.pricing.formatted_breakeven_price}<br/>"
                f"<b>Preco Alvo para Margem de 15%:</b> {report.pricing.formatted_price_at_15_margin}<br/>"
                f"<b>Preco Alvo para Margem de 20%:</b> {report.pricing.formatted_price_at_20_margin}<br/>"
                f"<b>Limite de Desconto em Campanhas:</b> {report.pricing.formatted_markdown_budget}<br/>"
            )
            story.append(Paragraph(p_text, body_style))
            
            story.append(Paragraph("<b>Canal de Importacao e Logistica Recomendas:</b>", bold_body_style))
            log_text = (
                f"Canal recomendado: {report.inventory.recommended_import_channel}<br/>"
                f"Tempo de reabastecimento estimado: {report.inventory.replenishment_lead_time_days} dias<br/>"
                f"Quantidade Minima de Pedido (MOQ): {report.inventory.recommended_moq} unidades<br/>"
                f"Estoque de Seguranca Minimo: {report.inventory.recommended_safety_stock} unidades"
            )
            story.append(Paragraph(log_text, body_style))
            story.append(Spacer(1, 10))

            # 7. D部分：行动落地指令清单 (Plano de Ação)
            story.append(Paragraph("D. Plano de Acao Recomendado (Sugestoes de Execucao)", section_style))
            for idx, action in enumerate(report.recommendations.action_items_list, 1):
                # 巴西语形式的前缀，并剥除不可在 Helvetica 中渲染的非标准宽字符以保万全
                safe_action = action.replace("【", "[").replace("】", "]").replace("‘", "'").replace("’", "'")
                story.append(Paragraph(f"<b>Passo {idx}:</b> {safe_action}", body_style))

            # 8. 编译组装 PDF 文件
            doc.build(story)

            return ExportResult(
                success=True,
                file_path=os.path.abspath(output_path),
                message=f"成功将财务诊断与选品分析白皮书编译并导出为 PDF 文档！物理路径: {output_path}"
            )
        except Exception as e:
            return ExportResult(
                success=False,
                file_path="",
                message=f"PDF 导出运行异常: {str(e)}",
                errors=[f"ReportLab PDF compile or draw error: {str(e)}"]
            )
