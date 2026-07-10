# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 巴西本土与进口税率精算器
负责精算 Simples Nacional 阶梯税、州内及跨州 ICMS 流转税、IPI 工业税、PIS/COFINS、
以及跨境合规计划 (Remessa Conforme) 进口税（含内含税算法）。
"""

from src.calculators.fee_calculator import load_taxes_config
from src.models.product import Product
from src.utils.money import round_to_two, calculate_percentage

class TaxCalculator:
    """
    税费计算器 (SOLID - 单一职责)
    精算巴西本土公司所涉及的全部税制与跨境进口环节税率。
    """

    def __init__(self) -> None:
        # 一次性加载 taxes_brazil.yaml 配置文件
        self.taxes = load_taxes_config()

    def calculate_simples_nacional_rate(self, annual_revenue_brl: float) -> float:
        """
        计算 Simples Nacional 的有效税率 (Alíquota Efetiva)
        
        计算公式：
            有效税率 = (过去12个月累计营业额 * 标称税率 - 速算扣除数) / 过去12个月累计营业额
            
        Args:
            annual_revenue_brl: 过去12个月累计营业额 (BRL)
            
        Returns:
            float: 有效税率浮点数 (例如 0.0532 代表 5.32%)
        """
        brackets = self.taxes["simples_nacional"]["brackets"]
        
        if annual_revenue_brl <= 0.0:
            # 默认为最底档 nominal 税率
            return float(brackets[0]["nominal_rate"])
            
        # 寻找对应的梯度
        selected = brackets[0]
        for b in brackets:
            min_rev = float(b["min_annual_revenue_brl"])
            max_rev = float(b["max_annual_revenue_brl"])
            if min_rev <= annual_revenue_brl <= max_rev:
                selected = b
                break
        else:
            # 超过 480w 的封顶挡或默认最后一档
            selected = brackets[-1]
            
        nominal_rate = float(selected["nominal_rate"])
        deduction_brl = float(selected["deduction_brl"])
        
        # 计算有效税率
        effective_rate = (annual_revenue_brl * nominal_rate - deduction_brl) / annual_revenue_brl
        return max(effective_rate, 0.0)

    def calculate_simples_nacional_tax(self, selling_price_brl: float, annual_revenue_brl: float) -> float:
        """
        计算单笔交易所产生的 Simples Nacional 本土税额
        """
        rate = self.calculate_simples_nacional_rate(annual_revenue_brl)
        return calculate_percentage(selling_price_brl, rate)

    def calculate_icms(self, price_brl: float, origin_state: str, dest_state: str, is_imported_good: bool = False) -> float:
        """
        计算本土交易产生的 ICMS 流转税 (仅针对非 Simples Nacional 的一般纳税人)
        
        Args:
            price_brl: 交易金额
            origin_state: 发货州名称缩写 (如 'SP')
            dest_state: 目的州名称缩写 (如 'RJ')
            is_imported_good: 商品是否为进口件 (进口件跨州统一征收 4% ICMS)
            
        Returns:
            float: ICMS 税额
        """
        icms_cfg = self.taxes["icms"]
        origin = origin_state.upper().strip()
        dest = dest_state.upper().strip()
        
        # 1. 州内流转 (同州交易)
        if origin == dest:
            rate = icms_cfg["intra_state"].get(dest, icms_cfg["intra_state"]["default"])
            return calculate_percentage(price_brl, rate)
            
        # 2. 跨州流转 (异州交易)
        if is_imported_good:
            # 进口商品跨州流通，税率为统一的 4%
            rate = icms_cfg["inter_state"]["imported_good_inter_state_rate"]
        else:
            # 普通国产货物跨州
            origin_cfg = icms_cfg["inter_state"].get(f"origin_{origin}", {})
            # 寻找目的州的特指折扣 (如 SP_TO_ES 为 7%, 圣保罗发往东北部 NE 为 7%)
            if dest in ("ES", "BA", "PE", "CE", "MA", "AL", "PB", "RN", "SE", "PI"):
                # 巴西东南部发往北部、东北部、中西部，税率通常为 7%
                rate = origin_cfg.get("to_ES", 0.07) # 这里的 to_ES 与 to_NE 均配置为了 7%
            else:
                rate = origin_cfg.get(f"to_{dest}", icms_cfg["inter_state"]["default_inter_state_rate"])
                
        return calculate_percentage(price_brl, rate)

    def calculate_pis_cofins(self, price_brl: float, regime: str = "cumulative") -> float:
        """
        计算本土交易产生的 PIS 与 COFINS 合计税金 (仅针对一般纳税人)
        
        Args:
            price_brl: 交易金额
            regime: 税务模式 (cumulative: 估算利润制，共 3.65%; non_cumulative: 实际利润制，共 9.25%)
        """
        if regime == "cumulative":
            pis_rate = self.taxes["pis"]["cumulative_regime"]["rate"]
            cof_rate = self.taxes["cofins"]["cumulative_regime"]["rate"]
        else:
            pis_rate = self.taxes["pis"]["non_cumulative_regime"]["rate"]
            cof_rate = self.taxes["cofins"]["non_cumulative_regime"]["rate"]
            
        total_rate = pis_rate + cof_rate
        return calculate_percentage(price_brl, total_rate)

    def calculate_ipi(self, cost_price_brl: float, category: str) -> float:
        """
        计算产品采购/进口环节承担的 IPI 工业税
        """
        ipi_cfg = self.taxes["ipi"]
        category_key = category.lower().strip()
        rate = ipi_cfg["rates_by_category"].get(category_key, ipi_cfg["rates_by_category"]["default"])
        return calculate_percentage(cost_price_brl, rate)

    def calculate_remessa_conforme(self, declared_value_usd: float, exchange_rate: float = 5.0) -> float:
        """
        精算跨境合规直邮（Remessa Conforme）下的海关进口税金
        
        计算公式 (巴西法定内含税算法 Cálculo por Dentro)：
            1. 进口关税 (Federal Tax) = 申报价值 * 进口税率 (若超过50美元，减去12美元扣除额)
            2. 进口税基 (ICMS Base) = (申报价值 + 进口关税) / (1 - ICMS税率)
            3. ICMS 税金 = 进口税基 * ICMS税率
            4. 总税金 (USD) = 进口关税 + ICMS 税金
            5. 总税金 (BRL) = 总税金 (USD) * 汇率
            
        Args:
            declared_value_usd: 包裹的美元申报价值
            exchange_rate: 美元兑雷亚尔汇率 (如 5.0)
            
        Returns:
            float: 折算为雷亚尔 (BRL) 的总进口税金 (保留两位小数)
        """
        rc = self.taxes["import_taxes"]["remessa_conforme"]
        threshold = float(rc["threshold_usd"])
        
        # 1. 判断是否超过 50 美元起征点
        if declared_value_usd <= threshold:
            # 50美元以下：20% 联邦税 + 17% 进口 ICMS
            fed_rate = float(rc["under_threshold"]["federal_import_tax_rate"])
            icms_rate = float(rc["under_threshold"]["icms_rate"])
            fed_tax = declared_value_usd * fed_rate
        else:
            # 50美元以上：60% 联邦税 (有12美元扣减) + 17% 进口 ICMS
            fed_rate = float(rc["over_threshold"]["federal_import_tax_rate"])
            icms_rate = float(rc["over_threshold"]["icms_rate"])
            deduction = float(rc["over_threshold"]["deduction_usd"])
            fed_tax = max(declared_value_usd * fed_rate - deduction, 0.0)
            
        # 2. 内含税计算 ICMS Base = (declared_value_usd + fed_tax) / (1 - 0.17)
        icms_base = (declared_value_usd + fed_tax) / (1.0 - icms_rate)
        icms_tax = icms_base * icms_rate
        
        # 3. 汇总美元总税金并折算 BRL
        total_tax_usd = fed_tax + icms_tax
        total_tax_brl = total_tax_usd * exchange_rate
        
        return round_to_two(total_tax_brl)
