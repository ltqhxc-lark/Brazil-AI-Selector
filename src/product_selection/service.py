# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 选品分析综合业务服务层
集成了已有财务试算、物理体积重、多维度打分评级逻辑，以及 SQLAlchemy 数据库仓储持久化能力。
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from src.models.product import Product
from src.models.platform import Platform
from src.services.profit_service import ProfitService
from src.services.fee_service import FeeService
from src.services.tax_service import TaxService
from src.calculators.shipping_calculator import ShippingCalculator
from src.product_selection.models import MarketData, SelectionCriteria, SelectionResult
from src.product_selection.calculator import ProductSelectionCalculator
from src.product_selection.scoring import ProductScoringEngine
from src.product_selection.recommendation import SelectionRecommender
from src.product_selection.db_models import SelectionProductDB, SelectionMarketDataDB, SelectionResultDB
from src.product_selection.repository import ProductRepository, MarketDataRepository, SelectionResultRepository

logger = logging.getLogger(__name__)

class ProductSelectionService:
    """
    选品综合分析服务层
    """

    def __init__(
        self,
        profit_service: Optional[ProfitService] = None,
        fee_service: Optional[FeeService] = None,
        tax_service: Optional[TaxService] = None,
        shipping_calculator: Optional[ShippingCalculator] = None
    ) -> None:
        """
        依赖注入已有服务与计算器，避免复制计算逻辑。
        """
        self._profit_service = profit_service or ProfitService()
        self._fee_service = fee_service or FeeService()
        self._tax_service = tax_service or TaxService()
        self._shipping_calculator = shipping_calculator or ShippingCalculator()

    def evaluate_product(
        self,
        product: Product,
        market_data: MarketData,
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> SelectionResult:
        """
        [纯内存业务] 评估单款商品的选品可行性并输出综合报告 (不包含任何数据库持久化读写)。
        """
        criteria = criteria or SelectionCriteria()

        temp_platform = Platform(
            platform_id=platform_id,
            platform_name=platform_name,
            selling_price_brl=market_data.average_selling_price_brl
        )

        fee_res = self._fee_service.get_fee_analysis(product, temp_platform)
        platform_fee_ratio = fee_res.fee_to_revenue_ratio
        
        tax_res = self._tax_service.get_tax_analysis(product, temp_platform)
        tax_ratio = tax_res.effective_tax_rate
        
        shipping_fee_brl = self._shipping_calculator.calculate(product, temp_platform)

        estimated_retail_price = ProductSelectionCalculator.calculate_estimated_selling_price(
            cost_price_brl=product.cost_price_brl,
            estimated_shipping_brl=shipping_fee_brl,
            platform_fee_ratio=platform_fee_ratio,
            tax_ratio=tax_ratio,
            target_margin_ratio=criteria.min_net_margin
        )

        final_platform = Platform(
            platform_id=platform_id,
            platform_name=platform_name,
            selling_price_brl=estimated_retail_price
        )

        profit_res = self._profit_service.calculate_profitability(product, final_platform)

        estimated_net_profit = profit_res.net_profit
        estimated_margin = profit_res.margin
        estimated_roi = ProductSelectionCalculator.calculate_roi(estimated_net_profit, product.cost_price_brl)
        estimated_gross_profit = estimated_retail_price - product.cost_price_brl

        scores = ProductScoringEngine.calculate_scores(
            product=product,
            market_data=market_data,
            estimated_margin=estimated_margin,
            estimated_roi=estimated_roi,
            criteria=criteria
        )

        reasons = []
        warnings = []

        if scores.recommendation_level == "S":
            reasons.append(f"产品打分极高 ({scores.total_score}分)，综合表现极其强劲。")
        elif scores.recommendation_level == "A":
            reasons.append(f"产品打分优异 ({scores.total_score}分)，具备高推荐度。")
        elif scores.recommendation_level == "B":
            reasons.append(f"产品打分及格 ({scores.total_score}分)，商业可行，建议谨慎跟进。")

        if estimated_roi >= criteria.target_roi:
            reasons.append(f"预期 ROI ({round(estimated_roi * 100, 2)}%) 达到或超过目标水平。")
        else:
            warnings.append(f"预期 ROI ({round(estimated_roi * 100, 2)}%) 未能达标。")

        if estimated_margin >= criteria.min_net_margin:
            reasons.append(f"预期净利率 ({round(estimated_margin * 100, 2)}%) 处于健康区间。")
        else:
            warnings.append(f"预期净利率 ({round(estimated_margin * 100, 2)}%) 偏低，利润空间不足。")

        vol_weight_g = ProductSelectionCalculator.calculate_volumetric_weight_g(product)
        if product.weight_g > criteria.overweight_threshold_g:
            warnings.append(f"商品实际重量为 {product.weight_g}g，已超过 {criteria.overweight_threshold_g}g 的轻量门槛。")
        if vol_weight_g > product.weight_g:
            warnings.append(f"商品体积重为 {vol_weight_g}g，显著超出物理实重，属于轻抛货物。")

        if market_data.demand_score >= criteria.demand_sales_thresholds.get("high", 8.0):
            reasons.append(f"市场需求极其旺盛 (需求评分: {market_data.demand_score}/10.0)。")
        if market_data.competitor_count >= criteria.competition_seller_thresholds.get("very_high_limit", 20):
            warnings.append(f"该品类竞争极度激烈，已有超过 {market_data.competitor_count} 家竞争卖家。")

        return SelectionResult(
            product=product,
            market_data=market_data,
            scores=scores,
            estimated_retail_price_brl=estimated_retail_price,
            estimated_net_profit_brl=estimated_net_profit,
            estimated_roi=estimated_roi,
            estimated_margin=estimated_margin,
            estimated_tax_brl=profit_res.total_tax,
            estimated_platform_fee_brl=profit_res.total_fee,
            estimated_shipping_brl=profit_res.total_shipping,
            estimated_gross_profit_brl=estimated_gross_profit,
            recommendation_reasons=reasons,
            risk_warnings=warnings
        )

    def evaluate_batch(
        self,
        products: List[Product],
        market_data_list: List[MarketData],
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> Tuple[List[SelectionResult], List[Tuple[str, str]]]:
        """
        [纯内存业务] 批量评估多款候选商品，支持部分商品失败不中断整体流程。
        """
        if len(products) != len(market_data_list):
            raise ValueError(
                f"商品列表与市场数据列表长度不一致，无法匹配。"
                f"(商品数量: {len(products)}, 市场数据数量: {len(market_data_list)})"
            )

        criteria = criteria or SelectionCriteria()
        results = []
        errors = []

        for prod, market in zip(products, market_data_list):
            try:
                res = self.evaluate_product(
                    product=prod,
                    market_data=market,
                    criteria=criteria,
                    platform_id=platform_id,
                    platform_name=platform_name
                )
                results.append(res)
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                sku = prod.sku if hasattr(prod, 'sku') else "Unknown"
                logger.error(f"商品 {sku} 选品试算评估失败，错误信息: {error_msg}")
                errors.append((sku, error_msg))

        ranked_results = SelectionRecommender.rank_and_filter(results, criteria)
        return ranked_results, errors

    # ==============================================================================
    # 数据库集成业务方法 (实现事务边界、调用 Repository 读写)
    # ==============================================================================

    def _evaluate_and_persist_single(
        self,
        session: Session,
        product: Product,
        market_data: MarketData,
        criteria: SelectionCriteria,
        platform_id: str,
        platform_name: str
    ) -> SelectionResultDB:
        """
        【内部私有辅助方法】执行单件商品的评估、打分并写入数据库（仅 flush，不单独管理事务）。
        """
        product_repo = ProductRepository(session)
        market_repo = MarketDataRepository(session)
        result_repo = SelectionResultRepository(session)

        # 1. 在数据库中创建或同步更新选品商品基础静态规格
        db_product = product_repo.get_by_sku(product.sku)
        if db_product:
            db_product = product_repo.update(
                product.sku,
                name=product.name,
                cost_price_brl=Decimal(str(product.cost_price_brl)),
                weight_g=Decimal(str(product.weight_g)),
                length_cm=Decimal(str(product.length_cm)),
                width_cm=Decimal(str(product.width_cm)),
                height_cm=Decimal(str(product.height_cm)),
                category=product.category,
                declared_value_usd=Decimal(str(product.declared_value_usd))
            )
        else:
            db_product = product_repo.create(
                sku=product.sku,
                name=product.name,
                cost_price_brl=Decimal(str(product.cost_price_brl)),
                weight_g=Decimal(str(product.weight_g)),
                length_cm=Decimal(str(product.length_cm)),
                width_cm=Decimal(str(product.width_cm)),
                height_cm=Decimal(str(product.height_cm)),
                category=product.category,
                declared_value_usd=Decimal(str(product.declared_value_usd))
            )

        # 2. 持久化本次市场评估条件
        db_market = market_repo.create(
            product_id=db_product.id,
            average_selling_price_brl=Decimal(str(market_data.average_selling_price_brl)),
            competitor_count=market_data.competitor_count,
            demand_score=Decimal(str(market_data.demand_score)),
            trend_factor=Decimal(str(market_data.trend_factor))
        )

        # 3. 运行已有的内存精算、反推与打分业务，绝对不复制公式
        res = self.evaluate_product(
            product=product,
            market_data=market_data,
            criteria=criteria,
            platform_id=platform_id,
            platform_name=platform_name
        )

        # 4. 持久化最终综合选品报告结果 (不 commit)
        db_result = result_repo.save_result(
            product_id=db_product.id,
            market_data_id=db_market.id,
            estimated_retail_price_brl=Decimal(str(res.estimated_retail_price_brl)),
            estimated_net_profit_brl=Decimal(str(res.estimated_net_profit_brl)),
            estimated_roi=Decimal(str(res.estimated_roi)),
            estimated_margin=Decimal(str(res.estimated_margin)),
            estimated_tax_brl=Decimal(str(res.estimated_tax_brl)),
            estimated_platform_fee_brl=Decimal(str(res.estimated_platform_fee_brl)),
            estimated_shipping_brl=Decimal(str(res.estimated_shipping_brl)),
            estimated_gross_profit_brl=Decimal(str(res.estimated_gross_profit_brl)),
            total_score=Decimal(str(res.scores.total_score)),
            profit_score=Decimal(str(res.scores.profit_score)),
            demand_score=Decimal(str(res.scores.demand_score)),
            competition_score=Decimal(str(res.scores.competition_score)),
            logistics_score=Decimal(str(res.scores.logistics_score)),
            recommendation_level=res.scores.recommendation_level,
            recommendation_reasons=res.recommendation_reasons,
            risk_warnings=res.risk_warnings
        )
        return db_result

    def evaluate_and_save_product(
        self,
        session: Session,
        product: Product,
        market_data: MarketData,
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> SelectionResultDB:
        """
        评估单款商品并将商品、市场瞬时条件以及评估结果报告持久化存储到数据库。
        
        事务边界：
            负责本业务边界的显式事务管理（commit / rollback），失败时回滚并原样向上抛出异常。
        """
        criteria = criteria or SelectionCriteria()
        try:
            db_result = self._evaluate_and_persist_single(
                session=session,
                product=product,
                market_data=market_data,
                criteria=criteria,
                platform_id=platform_id,
                platform_name=platform_name
            )
            session.commit()
            return db_result
        except Exception as e:
            session.rollback()
            raise e

    def evaluate_and_save_batch(
        self,
        session: Session,
        products: List[Product],
        market_data_list: List[MarketData],
        criteria: Optional[SelectionCriteria] = None,
        platform_id: str = "mercado_livre_brasil",
        platform_name: str = "Mercado Livre Brasil"
    ) -> Tuple[List[SelectionResultDB], List[Tuple[str, str]]]:
        """
        批量评估多款商品并将全部成功评估的选品持久化存储到数据库。
        
        容错性：
            单个商品因各种规格或约束异常发生失败时，记录错误详情并不中断整批。
            利用 SQLAlchemy 的 Savepoint (session.begin_nested())，使失败商品回滚至其自身的独立保存点。
            
        排序与过滤：
            符合 criteria.min_net_margin、criteria.target_roi 以及不属于 C 级的评估结果
            会组成最终结果集，并按照综合得分 total_score 由高到低（降序）进行排序呈报。
        """
        if len(products) != len(market_data_list):
            raise ValueError(
                f"商品列表与市场数据列表长度不一致，无法批量匹配。"
                f"(商品数量: {len(products)}, 市场数据数量: {len(market_data_list)})"
            )

        criteria = criteria or SelectionCriteria()
        results = []
        errors = []

        for prod, market in zip(products, market_data_list):
            # 对单个商品执行 Savepoint 嵌套事务，保障局部故障不影响其他商品状态
            nested_sp = session.begin_nested()
            try:
                db_result = self._evaluate_and_persist_single(
                    session=session,
                    product=prod,
                    market_data=market,
                    criteria=criteria,
                    platform_id=platform_id,
                    platform_name=platform_name
                )
                results.append(db_result)
            except Exception as e:
                # 回滚此单件商品的局部 savepoint
                nested_sp.rollback()
                error_msg = f"{type(e).__name__}: {str(e)}"
                sku = prod.sku if hasattr(prod, 'sku') else "Unknown"
                logger.error(f"商品 {sku} 批量评估持久化局部失败，错误信息: {error_msg}")
                errors.append((sku, error_msg))

        try:
            # 批量成功的商品提交持久化
            if results:
                session.commit()
        except Exception as e:
            session.rollback()
            raise e

        # 对最终评估成果应用推荐决策器的过滤条件（利润底线、ROI 达标线、C 级不推荐）并倒序排序
        filtered_results = []
        for r in results:
            # 过滤低于最低净利润率标准的选品
            if r.estimated_margin < Decimal(str(criteria.min_net_margin)):
                continue
            # 过滤低于最低 ROI 达标线的选品
            if r.estimated_roi < Decimal(str(criteria.target_roi)):
                continue
            # 过滤不推荐的 C 级选品
            if r.recommendation_level == "C":
                continue
            filtered_results.append(r)

        # 按照综合评分 total_score 降序（由高到低）进行排序
        ranked_results = sorted(filtered_results, key=lambda x: x.total_score, reverse=True)
        return ranked_results, errors

    def get_history(
        self,
        session: Session,
        product_id: Optional[int] = None,
        recommendation_level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SelectionResultDB]:
        """
        [数据库持久化集成接口] 查询历史选品报告详情清单，完全通过 SelectionResultRepository 读取。
        """
        result_repo = SelectionResultRepository(session)
        return result_repo.get_history(
            product_id=product_id,
            recommendation_level=recommendation_level,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit
        )

    def get_result_by_id(self, session: Session, result_id: int) -> Optional[SelectionResultDB]:
        """
        [数据库持久化集成接口] 根据主键 ID 调取单条历史决策报告，通过 SelectionResultRepository 读取。
        """
        result_repo = SelectionResultRepository(session)
        return result_repo.get_by_id(result_id)

