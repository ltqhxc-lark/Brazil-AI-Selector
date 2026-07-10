# Brazil-AI-Selector

**巴西出海选品、财务精算、多通道关税计提与综合商业决策自动化核算微服务系统 (v1.0.0)**

---

## 1. 项目简介

**Brazil-AI-Selector** 是一套专为中国跨境出海卖家和巴西本土电商零售企业打造的、企业级财务精算与决策支持系统。系统深度对接巴西极为复杂的税务框架（Tributação Brasileira），完全参数化了解析美客多（Mercado Livre）、虾皮（Shopee）和 TikTok Shop 巴西三大平台的最新本土店收费政策。通过将精密财务运算、启发式运营诊断规则以及多格式物理账本编译导出相结合，彻底扫除跨境出海卖家在巴西经营中的“账目黑箱”和“算不清账”的痛点。

---

## 2. 系统核心功能与设计架构

本系统严格遵循 **SOLID 软件设计原则** 与 **领域驱动设计 (DDD) 思想**。整体架构为典型的分层传递流水线，实现了模块间的高内聚、低耦合与零副作用：

```
Config (YAML 配置层)
   ↓
Database (数据库连接及 Session 基础设施)
   ↓
Models (纯净的领域 Dataclass 数据模型)
   ↓
Utils (高精度 Decimal 金额算术、重量换算与无 Locale 格式化)
   ↓
Validators (输入边界强校验与配置完好性安全网)
   ↓
Calculators (佣金、物流运费、流转税及 Remessa Conforme 精算引擎)
   ↓
Services (业务流程编排 Facade 与 Heuristic 诊断引擎)
   ↓
Platform Adapter (规则参数转换层)
   ↓
Strategy Engine (定价逆推、营销 PPC 预算、轻量化物流及备货决策)
   ↓
Report Domain (10 大嵌套报表 DTO 领域模型)
   ↓
Export Layer (Excel 审计工作表、PDF 商业诊断书、CSV、JSON 物理导出)
   ↓
REST API (基于 FastAPI 的安全、高并发、 traversal-proof 微服务路由层)
```

---

## 3. 快速开始与依赖安装

### 3.1 环境要求
- **Python 3.9+** (标准推荐)
- 支持的操作系统：Windows, macOS, Linux/Docker 容器

### 3.2 克隆与依赖安装
1. 克隆本项目并进入根目录。
2. 一键安装 `requirements.txt` 中指定的生产及测试所需的全部第三方依赖：
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. 外部规则配置文件说明

本系统所有扣点、运费、税耗和基本设置均从 `config/` 目录加载，**代码内 100% 杜绝硬编码**。

1. **`config/settings.yaml` (系统全局配置)**：
   管理存储路径（SQLite、exports/、cache/）、本地化规范（锁定币种为 `BRL`，语言 `pt-BR`，时区 `America/Sao_Paulo`）、以及 AI 模型（Gemini/OpenAI）密钥占位符。
2. **`config/platform_rules.yaml` (三大平台佣金与物流费率配置)**：
   - **Mercado Livre Brasil**：Classic / Premium 曝光率佣金、低价 R$ 6.00 固定费起征点、全套 Full 重量运费阶梯（7档，300g 到 30kg）与卖家信誉等级折扣。
   - **Shopee Brasil**：基础 14% 佣金、2% 交易费、2026 最新单件 R$ 3.00 固定手续费、免邮计划（FSS）6% 额外抽佣及 R$ 30.00 封顶费。
   - **TikTok Shop Brasil**：15% 基础佣金、单笔 R$ 1.00 处理费、新卖家 1.99% 让利开关及联盟达人带货比例限制。
3. **`config/taxes_brazil.yaml` (巴西复杂税制规则配置)**：
   - **Simples Nacional**：商业 Anexo I 附表的 1-6 档累计营业额名义税率与速算扣除数。
   - **ICMS**：圣保罗、里约热内卢等核心大州州内销售税率及圣保罗起发的跨州税率矩阵。
   - **PIS / COFINS / IPI**：累进与非累进模式税率，工业品分类 IPI 估算率。
   - **Remessa Conforme**：低于和超过 50 美元起征点的 20%/60% 联邦关税、17% 进口 ICMS（含内含税计算参数）。

---

## 5. 核心 API 路由服务规格接口

本微服务通过 **FastAPI** 框架向外暴露高可用 REST API，支持自动化 Swagger / OpenAPI 在线交互文档（通过浏览器访问 `http://localhost:8000/docs` 即可）。

### 5.1 GET `/health`
- **业务用途**：极速可用性检测。
- **返回 HTTP 状态**：`200 OK`
- **响应示例**：
  ```json
  {
    "status": "UP",
    "project_name": "Brazil-AI-Selector",
    "version": "1.0.0"
  }
  ```

### 5.2 POST `/api/v1/analysis`
- **业务用途**：单品财务分析与策略诊断。
- **请求负载 (Request Body)**：
  ```json
  {
    "product": {
      "sku": "BR-TOY-05",
      "name": "Brinquedo Educativo de Madeira",
      "cost_price_brl": 25.00,
      "weight_g": 1200.0,
      "length_cm": 20.0,
      "width_cm": 15.0,
      "height_cm": 12.0,
      "category": "toys",
      "declared_value_usd": 15.00
    },
    "platform": {
      "platform_id": "shopee_brasil",
      "platform_name": "Shopee Brasil",
      "selling_price_brl": 89.00,
      "seller_level": "normal",
      "participate_fss": true,
      "affiliate_rate": 0.0
    },
    "annual_revenue_brl": 150000.00,
    "is_cross_border": false
  }
  ```
- **返回 HTTP 状态**：`200 OK`
- **响应主要内容**：
  返回营收总计、实付纯利、高读性比率百分比、综合预警（Green/Yellow/Red），并附带全部分项平台扣点（佣金、固定费、准备金等）、销售税金、盈亏平衡临界定价和极具实操性的降重、避税运营文字建议。

### 5.3 POST `/api/v1/reports`
- **业务用途**：编译财务数据并物理导出多格式报表文件。
- **参数要求**：
  结构与分析接口一致，追加 `format` 字段（**仅限 `xlsx`, `pdf`, `csv`, `json`**）。
- **返回 HTTP 状态**：`201 Created`
- **响应示例**：
  ```json
  {
    "success": true,
    "file_path": "/api/v1/reports/report_BR-TOY-05_shopee_brasil.xlsx",
    "filename": "report_BR-TOY-05_shopee_brasil.xlsx",
    "format": "xlsx",
    "message": "成功将财务诊断与运营分析白皮书导出为精美 Excel 工作表！"
  }
  ```

### 5.4 GET `/api/v1/reports/{filename}`
- **业务用途**：安全流式传送物理报表。
- **安全保障**：
  - **白名单限制**：只允许下载 `xlsx`, `pdf`, `csv`, `json` 后缀文件，其余（如 `.py`, `.env`）直接拦截。
  - **防目录穿越 (Anti-Path Traversal)**：基于 `Path.resolve().is_relative_to()`，彻底碎裂一切包含 `..` 或 URL 转义字符的穿越请求，保护服务器绝对物理隐私。

---

## 6. 自带极简一键冒烟测试运行

我们已内置了全套数据流向的一键编译检测，你可以通过在终端运行以下 Python 命令进行秒级核对：
```bash
python -m compileall src
```
若需要启动 API 独立服务进行开发及集成：
```bash
# 启动本地 Uvicorn ASGI 服务
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 7. 安全与防穿透核准说明
1. **输入防御**：Pydantic 拦截器在 API 边缘强校验，一切采购价、售价等字段为负值、或者物理重量尺寸为非正值直接熔断（测试返回 422），绝不让任何脏数据污染底层精算模型，完全屏蔽了逻辑层产生除零、负溢出等技术隐患。
2. **安全隔离**：响应中**绝不返回任何服务器物理路径（如 D:\Brazil...）**，仅返回 `/api/v1/reports/...` 掩膜；全局 API Key 或底层敏感环境变量一律不参与响应序列化。
