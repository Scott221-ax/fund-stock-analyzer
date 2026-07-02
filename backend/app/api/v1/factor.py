"""因子发掘 API

路由前缀：/api/v1/factor
当前阶段为 Mock 实现，用于演示前端 Dashboard UI。
生产环境下应替换为真实的因子计算引擎：
  - 读取 factor_df（日频因子矩阵）和 return_df（日频收益率矩阵）
  - 调用 IC/IR 检验函数与五分层回测函数
  - 返回真实计算结果

Mock 策略：
  - 以 expression 的哈希值为随机种子，保证同一表达式返回相同结果
  - 按 Q5 > Q4 > Q3 > Q2 > Q1 的期望收益生成序列，模拟有效因子的分层效果
  - 加入正态分布随机噪声，使曲线更接近真实历史净值走势
"""
import asyncio
import hashlib
import math
import random
from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...models.schemas import ApiResponse

router = APIRouter(prefix="/api/v1/factor", tags=["factor"])


# ── 请求模型 ─────────────────────────────────────────────────

class FactorMineRequest(BaseModel):
    data_source:       str   = Field("fund_nav",    description="数据源标识")
    expression:        str   = Field(...,           description="因子表达式")
    start_date:        str   = Field("2020-01-01",  description="回测起始日期")
    end_date:          str   = Field("",            description="回测结束日期，空则取今日")
    rebalance_period:  str   = Field("monthly",     description="调仓周期: monthly | weekly")
    prediction_window: int   = Field(20,            description="预测窗期（天数）: 5 | 20")


# ── 工具函数 ─────────────────────────────────────────────────

def _expr_seed(expression: str) -> int:
    """根据因子表达式生成确定性随机种子，保证相同表达式结果可复现。"""
    return int(hashlib.md5(expression.strip().encode()).hexdigest()[:8], 16)


def _generate_dates(
    start: str,
    end: str,
    period: str,
) -> list[str]:
    """生成调仓日期序列。

    Args:
        start:  起始日期字符串 'YYYY-MM-DD'
        end:    结束日期字符串，空则取今日
        period: 'monthly' 或 'weekly'

    Returns:
        日期字符串列表，格式 'YYYY-MM-DD'
    """
    try:
        dt_start = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        dt_start = datetime(2020, 1, 1)

    if end:
        try:
            dt_end = datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            dt_end = datetime.today()
    else:
        dt_end = datetime.today()

    # 结束日期不超过今日
    dt_end = min(dt_end, datetime.today())

    dates: list[str] = []
    current = dt_start
    step = timedelta(weeks=1) if period == "weekly" else None

    while current <= dt_end:
        dates.append(current.strftime("%Y-%m-%d"))
        if period == "weekly":
            current += timedelta(weeks=1)
        else:
            # 月度：下一个月 1 日
            month = current.month + 1
            year  = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            current = datetime(year, month, 1)

    return dates


def _simulate_equity_curves(
    dates: list[str],
    seed:  int,
    prediction_window: int,
) -> dict[str, list[float]]:
    """生成五分组（Q1~Q5）累计净值曲线。

    Q5（因子最高组）整体趋势最优，Q1 最差，
    各组叠加不同强度的正态随机噪声，使曲线更贴近真实市场走势。

    Args:
        dates:             日期序列
        seed:              随机种子（来自因子表达式哈希）
        prediction_window: 预测窗期（5 或 20 天）

    Returns:
        {"Q1": [...], "Q2": [...], ..., "Q5": [...]}
    """
    rng = random.Random(seed)

    # 每个周期的期望收益率（年化）：Q1 最低，Q5 最高
    # prediction_window 越大，分层效果越显著
    spread_factor = 1.0 + (prediction_window - 5) / 30.0   # 5→1.0, 20→1.5
    annual_drifts = {
        "Q1": (-0.08 - rng.uniform(0, 0.04)) * spread_factor,
        "Q2": (-0.02 + rng.uniform(-0.02, 0.02)),
        "Q3":  (0.03 + rng.uniform(-0.02, 0.03)),
        "Q4":  (0.08 + rng.uniform(0,  0.03)),
        "Q5":  (0.14 + rng.uniform(0,  0.05)) * spread_factor,
    }
    # 波动率（年化）
    annual_vols = {q: 0.12 + rng.uniform(0, 0.05) for q in annual_drifts}

    n = len(dates)
    # 每期时间步长（近似：月度 = 1/12 年，周度 = 1/52 年）
    dt = 1 / 12 if n > 0 and (n < 50) else 1 / 52

    curves: dict[str, list[float]] = {}
    for group, drift in annual_drifts.items():
        nav = 1.0
        series: list[float] = [round(nav, 4)]
        vol = annual_vols[group]
        for _ in range(n - 1):
            # 几何布朗运动：dS = S*(μ*dt + σ*sqrt(dt)*Z)
            z     = rng.gauss(0, 1)
            ret   = drift * dt + vol * math.sqrt(dt) * z
            nav  *= (1 + ret)
            nav   = max(nav, 0.1)   # 净值不低于 0.1（防止负值）
            series.append(round(nav, 4))
        curves[group] = series

    return curves


def _compute_mock_metrics(
    seed:              int,
    prediction_window: int,
) -> dict:
    """生成 IC / IR / 胜率 / 多空超额收益的 Mock 指标。

    Args:
        seed:              来自因子表达式哈希的随机种子
        prediction_window: 预测窗期

    Returns:
        包含 ic_mean / ic_ir / win_rate / long_short_return 的字典
    """
    rng = random.Random(seed + 42)   # 加偏移，避免与净值曲线共享相同数列

    # 预测窗期越长，IC 稳定性通常略低但量级可能更大
    ic_base  = 0.04 + rng.uniform(-0.02, 0.06)
    ic_ir    = 0.35 + rng.uniform(-0.10, 0.55)
    win_rate = 52.0 + rng.uniform(-8, 16)
    ls_ret   = 10.0 + rng.uniform(-5, 15) * (prediction_window / 10.0)

    return {
        "ic_mean":           round(ic_base,  4),
        "ic_ir":             round(ic_ir,    2),
        "win_rate":          round(win_rate, 1),
        "long_short_return": round(ls_ret,   1),
    }


# ── 端点 ─────────────────────────────────────────────────────

@router.post("/mine", summary="运行因子发掘（Mock）")
async def mine_factor(req: FactorMineRequest):
    """运行因子发掘计算，返回五分组净值曲线与有效性指标。

    当前实现为 Mock，使用因子表达式哈希作为随机种子生成确定性数据。
    相同表达式输入将返回相同结果，便于 UI 调试与演示。
    """
    if not req.expression.strip():
        return ApiResponse(code=400, message="因子表达式不能为空", data=None)

    # 模拟计算延迟（让前端 loading 状态更真实）
    await asyncio.sleep(0.8 + random.uniform(0, 0.6))

    seed  = _expr_seed(req.expression)
    dates = _generate_dates(req.start_date, req.end_date, req.rebalance_period)

    if len(dates) < 3:
        return ApiResponse(code=400, message="回测时间范围过短，至少需要 3 个调仓周期", data=None)

    curves  = _simulate_equity_curves(dates, seed, req.prediction_window)
    metrics = _compute_mock_metrics(seed, req.prediction_window)

    return ApiResponse(
        code=200,
        message="success",
        data={
            "expression":  req.expression,
            "dates":       dates,
            "groups":      curves,
            "metrics":     metrics,
        },
    )
