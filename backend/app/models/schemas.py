"""Pydantic 请求/响应模型"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# ─── 持仓相关 ───────────────────────────────────────────

class HoldingBase(BaseModel):
    """单只持仓记录"""
    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field("", description="基金名称")
    shares: float = Field(0, description="持有份额")
    cost_basis: float = Field(0, description="持仓成本")
    current_value: float = Field(0, description="当前市值")
    account: str = Field("default", description="账户标识")


class PortfolioSummary(BaseModel):
    """持仓总览"""
    total_value: float = 0
    total_cost: float = 0
    total_return: float = 0
    total_return_pct: float = 0
    fund_count: int = 0
    holdings: list[HoldingBase] = []


# ─── 基金数据相关 ──────────────────────────────────────

class FundInfo(BaseModel):
    """基金基本信息"""
    code: str
    name: str
    type: str = ""  # 股票型/混合型/债券型/指数型/货币型
    manager: str = ""
    company: str = ""
    establish_date: Optional[date] = None
    nav: float = 0       # 最新净值
    nav_date: Optional[date] = None


class FundNavHistory(BaseModel):
    """基金净值历史"""
    code: str
    date: date
    nav: float       # 单位净值
    acc_nav: float   # 累计净值


class FundEvalResult(BaseModel):
    """基金评价结果"""
    code: str
    name: str
    score: float = 0        # 综合评分 0-100
    return_rank: float = 0  # 收益排名百分位 0-100
    risk_level: str = ""    # 风险等级
    sharpe: float = 0       # 夏普比率
    max_drawdown: float = 0 # 最大回撤
    fee_rate: float = 0     # 综合费率


# ─── 市场扫描相关 ──────────────────────────────────────

class IndexValuation(BaseModel):
    """指数估值"""
    index_name: str
    index_code: str
    pe: float = 0
    pe_percentile: float = 0   # PE 历史百分位
    pb: float = 0
    pb_percentile: float = 0
    yield_ratio: float = 0     # 股息率


class MarketOverview(BaseModel):
    """市场概览"""
    indices: list[IndexValuation] = []
    stock_bond_ratio: float = 0  # 股债性价比
    north_flow: float = 0        # 北向资金今日净流入
    avg_pe_percentile: float = 0


# ─── 通用 ──────────────────────────────────────────────

class ApiResponse(BaseModel):
    """统一响应包装"""
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None



# === 交易回测模型 ===

class BacktestRequest(BaseModel):
    name: str = "自定义策略"
    target_code: str = "000300"
    target_name: str = "沪深300"
    target_type: str = "index"  # index or fund
    initial_capital: float = 100000
    position_size: float = 10000
    entry_rules: list[dict] = []
    exit_rules: list[dict] = []
    start_date: str = "2020-01-01"
    end_date: str = ""


class TradeRecord(BaseModel):
    entry_date: str = ""
    entry_price: float = 0
    exit_date: str = ""
    exit_price: float = 0
    shares: float = 0
    return_pct: float = 0
    profit: float = 0
    exit_reason: str = ""


class BacktestResult(BaseModel):
    strategy_name: str = ""
    target_name: str = ""
    initial_capital: float = 100000
    final_equity: float = 0
    total_return_pct: float = 0
    annualized_return: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    avg_win_pct: float = 0
    avg_loss_pct: float = 0
    profit_factor: float = 0
    trades: list[TradeRecord] = []
    equity_curve: list[dict] = []


# === 交易策略管理模型 ===

class StrategyBase(BaseModel):
    """策略公共字段（新建/更新共享）"""
    name:            str   = Field(...,   description="策略名称")
    description:     str   = Field("",   description="策略备注")
    target_code:     str   = Field(...,   description="标的代码，如 000300")
    target_name:     str   = Field("",   description="标的名称")
    target_type:     str   = Field("index", description="标的类型：index | fund")
    initial_capital: float = Field(100000.0, description="初始资金")
    position_size:   float = Field(10000.0,  description="每笔仓位金额")
    start_date:      str   = Field(...,   description="回测起始日期，格式 YYYY-MM-DD")
    end_date:        str   = Field("",   description="回测结束日期，为空则取当天")
    entry_rules:     list[dict] = Field(default_factory=list, description="入场规则列表")
    exit_rules:      list[dict] = Field(default_factory=list, description="出场规则列表")


class StrategyCreate(StrategyBase):
    """创建策略的请求体"""
    pass


class StrategyUpdate(StrategyBase):
    """更新策略的请求体（全量替换）"""
    pass


class StrategyResponse(StrategyBase):
    """策略响应体（含 id 与时间戳）"""
    id:         int = Field(..., description="策略 ID")
    created_at: str = Field(..., description="创建时间 UTC ISO-8601")
    updated_at: str = Field(..., description="更新时间 UTC ISO-8601")

    # 允许从 ORM 对象直接构建（from_attributes 替代 orm_mode）
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# 基金穿透实时估值 Pydantic 模型
# ═══════════════════════════════════════════════════════════════

class StockHoldingQuote(BaseModel):
    """单只持仓股实时行情快照"""
    stock_code:    str            = Field(..., description="股票代码（6位）")
    stock_name:    str            = Field(..., description="股票名称")
    weight:        float          = Field(..., description="持仓权重（小数，如 0.092 = 9.2%）")
    weight_pct:    float          = Field(..., description="持仓权重（百分比，如 9.2）")
    current_price: Optional[float]= Field(None, description="实时最新价（停牌/缺数时为 null）")
    change_pct:    float          = Field(..., description="实时涨跌幅（%，如 0.32 = +0.32%）")
    contribution:  float          = Field(..., description="对基金预估净值的贡献（百分点）")
    status:        str            = Field(..., description="normal | suspended | data_missing")


class IndexProxyQuote(BaseModel):
    """基准指数代理（剩余权重）"""
    index_code:  str   = Field(..., description="指数代码")
    index_name:  str   = Field(..., description="指数名称")
    weight:      float = Field(..., description="代理权重（= 1 - 前十大权重合计）")
    weight_pct:  float = Field(..., description="代理权重（百分比）")
    change_pct:  float = Field(..., description="指数实时涨跌幅（%）")
    contribution:float = Field(..., description="对预估净值的贡献（百分点）")
    status:      str   = Field(..., description="normal | data_missing")


class ValuationDataQuality(BaseModel):
    """估值数据质量报告"""
    disclosed_weight:    float = Field(..., description="前十大持仓权重合计（小数）")
    benchmark_weight:    float = Field(..., description="基准指数代理权重（小数）")
    stocks_total:        int   = Field(..., description="持仓股总数")
    stocks_normal:       int   = Field(..., description="获取到实时行情的股票数")
    stocks_suspended:    int   = Field(..., description="停牌股票数")
    stocks_data_missing: int   = Field(..., description="行情数据缺失的股票数")
    coverage_ratio:      float = Field(..., description="有效数据覆盖率（0.0~1.0）")
    is_reliable:         bool  = Field(..., description="估值可信度（coverage >= 60%）")


class FundValuationData(BaseModel):
    """基金穿透实时估值完整响应"""
    fund_code:            str                    = Field(..., description="基金代码")
    fund_name:            str                    = Field(..., description="基金名称")
    estimated_change_pct: float                  = Field(..., description="预估净值涨跌幅（%）")
    disclosed_holdings:   list[StockHoldingQuote]= Field(..., description="前十大持仓股明细")
    benchmark_proxy:      IndexProxyQuote         = Field(..., description="基准指数代理")
    data_quality:         ValuationDataQuality    = Field(..., description="数据质量报告")
    is_trading_hour:      bool                   = Field(..., description="是否为交易时段")
    updated_at:           str                    = Field(..., description="计算时间戳 ISO-8601")
