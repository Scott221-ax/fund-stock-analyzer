"""
基金穿透实时估值 API
===================

路由前缀：/api/v1/fund-valuation
供前端每分钟轮询，返回穿透持仓的加权盘中估值。

端点：
  GET /api/v1/fund-valuation/{fund_code}
    参数：fund_code  — 基金代码（6位数字，如 110011）
         refresh    — 是否强制刷新缓存（可选，默认 false）
    返回：穿透持仓明细 + 预估净值涨跌幅 + 数据质量报告
"""
import logging
import re

from fastapi import APIRouter, HTTPException, Query

from ...models.schemas import ApiResponse
from ...services.fund_valuation import FundValuationService, ValuationResult
from ... import util_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fund-valuation", tags=["fund-valuation"])

# 合法基金代码：6 位纯数字
_FUND_CODE_RE = re.compile(r"^\d{6}$")


def _serialize(result: ValuationResult) -> dict:
    """将 ValuationResult dataclass 转换为可序列化的 dict。"""
    return {
        "fund_code":            result.fund_code,
        "fund_name":            result.fund_name,
        "estimated_change_pct": result.estimated_change_pct,
        "is_trading_hour":      result.is_trading_hour,
        "updated_at":           result.updated_at,

        # 前十大持仓明细
        "disclosed_holdings": [
            {
                "stock_code":    q.stock_code,
                "stock_name":    q.stock_name,
                "weight":        q.weight,             # 小数，如 0.092
                "weight_pct":    round(q.weight * 100, 2),  # 百分比，如 9.2
                "current_price": q.current_price,
                "change_pct":    q.change_pct,
                "contribution":  q.contribution,       # 对估值的贡献（百分点）
                "status":        q.status,
            }
            for q in result.disclosed_holdings
        ],

        # 基准指数代理（剩余仓位）
        "benchmark_proxy": {
            "index_code":   result.benchmark_proxy.index_code,
            "index_name":   result.benchmark_proxy.index_name,
            "weight":       result.benchmark_proxy.weight,
            "weight_pct":   round(result.benchmark_proxy.weight * 100, 2),
            "change_pct":   result.benchmark_proxy.change_pct,
            "contribution": result.benchmark_proxy.contribution,
            "status":       result.benchmark_proxy.status,
        },

        # 数据质量摘要
        "data_quality": {
            "disclosed_weight":     result.data_quality.disclosed_weight,
            "benchmark_weight":     result.data_quality.benchmark_weight,
            "stocks_total":         result.data_quality.stocks_total,
            "stocks_normal":        result.data_quality.stocks_normal,
            "stocks_suspended":     result.data_quality.stocks_suspended,
            "stocks_data_missing":  result.data_quality.stocks_data_missing,
            "coverage_ratio":       result.data_quality.coverage_ratio,
            "is_reliable":          result.data_quality.is_reliable,
        },
    }


@router.get(
    "/{fund_code}",
    summary="基金穿透实时估值",
    description=(
        "穿透计算基金盘中预估净值涨跌幅。\n\n"
        "- 前十大重仓股实时行情（60s 缓存）\n"
        "- 剩余仓位以基准指数涨跌幅代理\n"
        "- 停牌/缺数时自动降级（涨跌幅置 0）\n"
        "- 非交易时段仍可调用，is_trading_hour=false 时结果为参考值"
    ),
)
async def get_fund_valuation(
    fund_code: str,
    refresh: bool = Query(
        default=False,
        description="强制刷新持仓缓存（true 时绕过 4h 缓存，重新从行情源拉取持仓数据）",
    ),
):
    """
    基金穿透实时估值接口。

    **请求示例**
    ```
    GET /api/v1/fund-valuation/110011
    GET /api/v1/fund-valuation/161725?refresh=true
    ```

    **返回字段说明**

    | 字段 | 类型 | 说明 |
    |------|------|------|
    | estimated_change_pct | float | 预估净值涨跌幅（%，如 0.42 = +0.42%）|
    | disclosed_holdings[] | list | 前十大持仓股明细 |
    | benchmark_proxy      | dict | 基准指数代理（剩余权重）|
    | data_quality         | dict | 数据质量摘要 |
    | is_trading_hour      | bool | 当前是否为交易时段 |
    | updated_at           | str  | 服务端计算时间戳（ISO-8601）|

    **status 字段取值**
    - `normal`       — 正常获取实时涨跌幅
    - `suspended`    — 该股票停牌（成交量=0），涨跌幅记为 0
    - `data_missing` — 行情数据缺失（停牌/数据源故障），涨跌幅记为 0

    **可靠性建议**
    `data_quality.coverage_ratio < 0.6` 时，`is_reliable=false`，
    前端应提示"数据覆盖不足，估值仅供参考"。
    """
    # ── 入参校验 ────────────────────────────────────────────
    if not _FUND_CODE_RE.match(fund_code.strip()):
        raise HTTPException(
            status_code=422,
            detail=f"基金代码格式错误：'{fund_code}'，应为6位纯数字（如 110011）",
        )

    # ── 强制刷新缓存（针对持仓数据）───────────────────────
    if refresh:
        cache_key = f"valuation:holdings:{fund_code.zfill(6)}"
        util_cache.clear(cache_key)
        logger.info("强制刷新持仓缓存 fund=%s", fund_code)

    # ── 调用服务层计算 ──────────────────────────────────────
    try:
        result: ValuationResult = await FundValuationService.calculate(fund_code)
    except ValueError as exc:
        # 业务错误（代码不存在、无持仓数据等）→ 404
        logger.warning("估值计算无数据 fund=%s: %s", fund_code, exc)
        return ApiResponse(code=200, message="success", data={
            "fund_code": fund_code, "fund_name": "", "estimated_change_pct": 0,
            "is_trading_hour": False, "updated_at": "",
            "disclosed_holdings": [],
            "benchmark_proxy": {"index_code":"","index_name":"","weight":0,"change_pct":0,"contribution":0,"status":"normal"},
            "data_quality": {"disclosed_weight":0,"benchmark_weight":0,"stocks_total":0,"stocks_normal":0,
                "stocks_suspended":0,"stocks_data_missing":0,"coverage_ratio":0,"is_reliable":False},
        })
    except Exception as exc:
        # 未预期错误 → 503（服务暂时不可用）
        logger.exception("估值计算未预期错误 fund=%s", fund_code)
        raise HTTPException(
            status_code=503,
            detail="估值服务暂时不可用，请稍后重试",
        )

    # ── 序列化并返回 ─────────────────────────────────────────
    return ApiResponse(code=200, message="success", data=_serialize(result))


@router.get(
    "/{fund_code}/holdings",
    summary="基金持仓快照（静态）",
    description="仅返回基金最新披露的前十大持仓，不含实时行情。用于首次渲染表格骨架。",
)
async def get_fund_holdings_only(fund_code: str):
    """
    仅返回持仓数据（无实时价格），速度快，可用于页面初始化。

    适合在"完整估值接口"返回前先填充表格结构。
    """
    if not _FUND_CODE_RE.match(fund_code.strip()):
        raise HTTPException(status_code=422, detail="基金代码格式错误")

    from ...services.fund_valuation import _fetch_holdings, _normalize
    try:
        fund_name, holdings = await _fetch_holdings(_normalize(fund_code))
    except Exception as exc:
        logger.exception("持仓快照拉取失败 fund=%s", fund_code)
        raise HTTPException(status_code=503, detail="持仓数据暂时不可用")

    if not holdings:
        return ApiResponse(code=200, message="success", data={"holdings": [], "fund_code": fund_code})

    return ApiResponse(
        code=200,
        message="success",
        data={
            "fund_code": fund_code.zfill(6),
            "fund_name": fund_name,
            "holdings": [
                {
                    "stock_code": h.stock_code,
                    "stock_name": h.stock_name,
                    "weight":     h.weight,
                    "weight_pct": round(h.weight * 100, 2),
                }
                for h in holdings
            ],
            "total_weight":     round(sum(h.weight for h in holdings), 4),
            "total_weight_pct": round(sum(h.weight for h in holdings) * 100, 2),
        },
    )
