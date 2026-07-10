# -*- coding: utf-8 -*-
"""
Brazil-AI-Selector - 外部配置文件结构与类型验证器
"""

import os
import yaml
from pathlib import Path
from src.validators import ValidationResult

# 定位项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def validate_config() -> ValidationResult:
    """
    全面核验 config/ 目录下三大核心配置文件的完整性与正确性
    
    核验目标：
        1. config/settings.yaml (系统全局设置)
        2. config/platform_rules.yaml (三大平台佣金与物流费率)
        3. config/taxes_brazil.yaml (巴西多税制阶梯及税率参数)
        
    校验规则：
        1. 物理文件必须真实存在
        2. 文件必须可以通过 YAML 引擎正确解析且不报语法错误
        3. 必须包含计算所要求的所有底层核心键名 (Required Keys)
        4. 部分极重要字段的类型必须正确 (如 debug 必须是布尔值)
        
    Returns:
        ValidationResult: 统一校验结果，失败时汇总所有文件、字段及解析层面的报错
    """
    errors = []
    
    # 待校验的三大文件和它们相对项目根目录的路径
    config_paths = {
        "settings": BASE_DIR / "config" / "settings.yaml",
        "platform_rules": BASE_DIR / "config" / "platform_rules.yaml",
        "taxes": BASE_DIR / "config" / "taxes_brazil.yaml"
    }
    
    loaded_configs = {}
    
    # === 阶段 1: 校验物理存在与语法解析 ===
    for name, path in config_paths.items():
        if not path.exists():
            errors.append(f"配置文件缺失: 无法在路径 '{path}' 找到 {name} 配置文件。")
            continue
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    errors.append(f"配置文件为空: '{path}' 解析得到的内容为 None。")
                else:
                    loaded_configs[name] = data
        except yaml.YAMLError as ye:
            errors.append(f"YAML 语法解析错误 ({name}): 在解析 '{path}' 时发生错误: {ye}")
        except Exception as e:
            errors.append(f"配置文件读取异常 ({name}): 读取 '{path}' 失败: {e}")

    # 若文件基本读取存在重大缺陷，立即返回汇总错误，不再进行深层字段匹配
    if errors:
        return ValidationResult(
            success=False,
            message=f"配置文件基础读取校验失败，共发现 {len(errors)} 处严重错误。",
            errors=errors
        )

    # === 阶段 2: settings.yaml 结构校验 ===
    if "settings" in loaded_configs:
        settings = loaded_configs["settings"]
        
        # 2.1 核查顶级分类
        for top_key in ["app_info", "localization", "storage", "config_files", "ai_config", "api_keys"]:
            if top_key not in settings:
                errors.append(f"settings.yaml 缺失顶级键: '{top_key}'。")
                
        # 2.2 核查 app_info 内子段与类型
        app_info = settings.get("app_info", {})
        if "project_name" not in app_info or not app_info["project_name"]:
            errors.append("settings.yaml 缺失必填字段: 'app_info.project_name'。")
        if "debug" in app_info and not isinstance(app_info["debug"], bool):
            errors.append(f"settings.yaml 字段类型错误: 'app_info.debug' 必须为 Boolean 类型，当前为 {type(app_info['debug']).__name__}。")
            
        # 2.3 核查 storage 内子段
        storage = settings.get("storage", {})
        for sub_key in ["database_url", "export_dir", "cache_dir", "temp_dir"]:
            if sub_key not in storage or not str(storage.get(sub_key, "")).strip():
                errors.append(f"settings.yaml 缺失存储路径配置: 'storage.{sub_key}'。")
                
        # 2.4 核查 config_files 内子段
        config_files = settings.get("config_files", {})
        for sub_key in ["platform_rules_path", "taxes_config_path"]:
            if sub_key not in config_files or not str(config_files.get(sub_key, "")).strip():
                errors.append(f"settings.yaml 缺失关联文件路径配置: 'config_files.{sub_key}'。")

    # === 阶段 3: platform_rules.yaml 结构校验 ===
    if "platform_rules" in loaded_configs:
        rules = loaded_configs["platform_rules"]
        
        # 3.1 核查三大平台顶级标识
        for platform_key in ["mercado_livre_brasil", "shopee_brasil", "tiktok_shop_brasil"]:
            if platform_key not in rules:
                errors.append(f"platform_rules.yaml 缺失必填平台规则: '{platform_key}'。")
                
        # 3.2 深入验证美客多规则子项
        ml = rules.get("mercado_livre_brasil", {})
        if "commission_rates" not in ml or "classic" not in ml.get("commission_rates", {}):
            errors.append("platform_rules.yaml 美客多缺失 'commission_rates.classic' 参数。")
        if "fixed_fee" not in ml or "fee_brl" not in ml.get("fixed_fee", {}):
            errors.append("platform_rules.yaml 美客多缺失 'fixed_fee.fee_brl' 低价固定费参数。")
        if "shipping" not in ml or "brackets" not in ml.get("shipping", {}):
            errors.append("platform_rules.yaml 美客多缺失 'shipping.brackets' 官方运费阶梯表。")
            
        # 3.3 深入验证虾皮规则子项
        shopee = rules.get("shopee_brasil", {})
        if "commission" not in shopee or "base_rate" not in shopee.get("commission", {}):
            errors.append("platform_rules.yaml 虾皮缺失 'commission.base_rate' 基础扣点。")
        if "free_shipping_program" not in shopee.get("commission", {}):
            errors.append("platform_rules.yaml 虾皮缺失 'commission.free_shipping_program' 免邮佣金参数。")
            
        # 3.4 深入验证 TikTok Shop 规则子项
        tiktok = rules.get("tiktok_shop_brasil", {})
        if "commission" not in tiktok or "base_rate" not in tiktok.get("commission", {}):
            errors.append("platform_rules.yaml TikTok Shop 缺失 'commission.base_rate' 基础佣金。")

    # === 阶段 4: taxes_brazil.yaml 结构校验 ===
    if "taxes" in loaded_configs:
        taxes = loaded_configs["taxes"]
        
        # 4.1 核心税项是否存在
        required_taxes = ["simples_nacional", "icms", "ipi", "pis", "cofins", "import_taxes", "icms_st", "difal"]
        for tax_key in required_taxes:
            if tax_key not in taxes:
                errors.append(f"taxes_brazil.yaml 缺失核心税务配置: '{tax_key}'。")
                
        # 4.2 深入校验 Simples Nacional 阶梯完整性
        sn = taxes.get("simples_nacional", {})
        if "brackets" not in sn or not isinstance(sn.get("brackets"), list) or len(sn.get("brackets", [])) != 6:
            errors.append("taxes_brazil.yaml 缺失合法的 Simples Nacional 6档阶梯税率表。")
            
        # 4.3 深入校验 ICMS 州内流转税SP基准
        icms = taxes.get("icms", {})
        if "intra_state" not in icms or "SP" not in icms.get("intra_state", {}):
            errors.append("taxes_brazil.yaml 缺失 ICMS 州内代表性大州（如 SP 圣保罗）的流转税。")
            
        # 4.4 深入校验跨境合规计划（Remessa Conforme）税率
        import_t = taxes.get("import_taxes", {})
        if "remessa_conforme" not in import_t or "under_threshold" not in import_t.get("remessa_conforme", {}):
            errors.append("taxes_brazil.yaml 进口税缺失 'remessa_conforme.under_threshold' (低额包裹) 税率规则。")

    # === 汇总并输出最后报告 ===
    if errors:
        return ValidationResult(
            success=False,
            message=f"配置文件字段及类型匹配失败，共校验 3 个文件，发现 {len(errors)} 处不合规项。",
            errors=errors
        )
    else:
        return ValidationResult(
            success=True,
            message="配置文件 (Settings, Platform Rules, Taxes) 的存在性、语法结构、键完整性、类型匹配 100% 校验通过。"
        )
