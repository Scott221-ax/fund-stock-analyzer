"""Pydantic 请求/响应模型"""
from datetime import date, datetime
from pydantic import BaseModel, Field
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
