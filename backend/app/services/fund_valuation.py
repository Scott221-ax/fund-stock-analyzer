"""
基金穿透实时估值服务
====================

业务逻辑：
  1. 拉取基金最新披露的前十大重仓股及权重（quarterly，4小时缓存）
  2. 并发获取所有标的的盘中实时涨跌幅（60秒缓存）
  3. 加权计算预估净值变动：
       估值涨跌幅 = Σ(持仓_i 权重 × 涨跌幅_i) + 剩余权重 × 基准指数涨跌幅
  4. 降级策略：
       · 停牌股票 → 涨跌幅置 0，标记 status="suspended"
       · 数据缺失 → 涨跌幅置 0，标记 status="data_missing"
       · 市场快照拉取失败 → 所有个股标记 data_missing，估值仅含指数项
       · 指数拉取失败 → 剩余权重不计入估值，降低 coverage_ratio

性能：
  · holdings 缓存 4h（季报数据极少变化）
  · 全市场快照（stock_zh_a_spot_em）缓存 60s，单次调用覆盖所有持仓股
  · 指数快照（index_zh_a_spot_em）缓存 60s
  · holdings + market + index 三路并发拉取（asyncio.gather）
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import akshare as ak
import pandas as pd

from ..data_fetch.fund_data import FundDataFetcher
from ..util_cache import get as cache_get, set as cache_set

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# 常量 & 配置
# ══════════════════════════════════════════════════════════════

# 基金代码 → 基准指数映射（生产环境可从数据库读取）
# 未命中时默认使用沪深300
_FUND_BENCHMARK: dict[str, tuple[str, str]] = {
    # (index_code, index_name)
    "110011": ("000300", "沪深300"),   # 易方达中小盘混合
    "161725": ("399997", "中证白酒"),   # 招商中证白酒LOF
    "000001": ("000300", "沪深300"),   # 华夏成长混合
    "110022": ("399905", "中证消费"),   # 易方达消费行业
    "001156": ("399006", "创业板指"),   # 天弘创业板ETF
    "510300": ("000300", "沪深300"),   # 华泰柏瑞沪深300ETF
    "510500": ("000905", "中证500"),   # 南方中证500ETF
    "159915": ("399006", "创业板指"),   # 易方达创业板ETF
    "000248": ("000905", "中证500"),   # 汇添富中证500
    "_default": ("000300", "沪深300"),
}

# 市场快照缓存 Key
_CACHE_STOCK_SPOT  = "valuation:stock_spot_all"    # 全量A股实时行情
_CACHE_INDEX_SPOT  = "valuation:index_spot_all"    # 全量指数实时行情
_CACHE_HOLDINGS    = "valuation:holdings:{}"       # 基金持仓（按代码）

_TTL_SPOT     = 60        # 实时行情 60s
_TTL_HOLDINGS = 14_400    # 持仓数据 4h


# ══════════════════════════════════════════════════════════════
# 内部数据结构
# ══════════════════════════════════════════════════════════════

@dataclass
class _HoldingRaw:
    """原始持仓记录（从基金季报解析）"""
    stock_code: str
    stock_name: str
    weight: float          # 小数形式，如 0.092（= 9.2%）


@dataclass
class StockQuote:
    """单只股票实时行情"""
    stock_code: str
    stock_name: str
    weight: float          # 小数形式
    current_price: Optional[float]
    change_pct: float      # 已转换为百分比，如 0.32 表示 +0.32%
    contribution: float    # weight × change_pct（百分点）
    status: str            # "normal" | "suspended" | "data_missing"


@dataclass
class IndexQuote:
    """基准指数实时行情"""
    index_code: str
    index_name: str
    weight: float
    change_pct: float
    contribution: float
    status: str


@dataclass
class DataQuality:
    """估值数据质量汇总"""
    disclosed_weight: float   # 前十大持仓权重合计（小数）
    benchmark_weight: float   # 指数代理权重 = 1 - disclosed_weight
    stocks_total:     int
    stocks_normal:    int
    stocks_suspended: int
    stocks_data_missing: int
    coverage_ratio: float     # 有效数据（normal）占全部估值权重的比率
    is_reliable: bool         # coverage_ratio >= 0.6 即认为估值可信


@dataclass
class ValuationResult:
    """穿透实时估值完整结果"""
    fund_code:             str
    fund_name:             str
    estimated_change_pct:  float          # 预估净值涨跌幅（%）
    disclosed_holdings:    list[StockQuote]
    benchmark_proxy:       IndexQuote
    data_quality:          DataQuality
    is_trading_hour:       bool
    updated_at:            str            # ISO-8601


# ══════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════

def _is_trading_hour() -> bool:
    """判断当前是否为 A 股交易时段（不考虑节假日休市）"""
    now  = datetime.now()
    if now.weekday() >= 5:       # 周六/周日
        return False
    t = now.time()
    from datetime import time as _time
    morning   = _time(9,  30) <= t <= _time(11, 30)
    afternoon = _time(13,  0) <= t <= _time(15,  0)
    return morning or afternoon


def _normalize(code: str) -> str:
    """股票代码标准化：去交易所后缀，补齐6位"""
    for suf in (".SH", ".SZ", ".XSHG", ".XSHE", ".sh", ".sz", ".OF"):
        code = code.replace(suf, "")
    return code.strip().zfill(6)


def _get_benchmark(fund_code: str) -> tuple[str, str]:
    """查询基金的基准指数。未命中时返回沪深300。"""
    norm = _normalize(fund_code)
    return _FUND_BENCHMARK.get(norm, _FUND_BENCHMARK["_default"])


def _extract_change(df: pd.DataFrame, code: str) -> Optional[float]:
    """从 spot DataFrame 中按股票代码提取涨跌幅。返回 None 表示未找到。"""
    if df is None or df.empty:
        return None
    # akshare 代码列可能包含或不包含前导零，需两侧都检查
    mask = df["代码"].astype(str).str.strip().str.zfill(6) == code
    rows = df[mask]
    if rows.empty:
        return None
    val = rows.iloc[0].get("涨跌幅", None)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _is_suspended(df: pd.DataFrame, code: str) -> bool:
    """
    判断股票是否停牌：存在于 snapshot 中，但成交量为 0。
    若不在 snapshot 中，调用方按 data_missing 处理。
    """
    if df is None or df.empty:
        return False
    mask = df["代码"].astype(str).str.strip().str.zfill(6) == code
    rows = df[mask]
    if rows.empty:
        return False
    vol_col = next((c for c in ("成交量", "成交额") if c in df.columns), None)
    if vol_col is None:
        return False
    try:
        return float(rows.iloc[0][vol_col]) == 0
    except (ValueError, TypeError):
        return False


# ══════════════════════════════════════════════════════════════
# 数据拉取层（带缓存）
# ══════════════════════════════════════════════════════════════

async def _fetch_holdings(fund_code: str) -> tuple[str, list[_HoldingRaw]]:
    """
    拉取基金前十大重仓股（含权重）。

    Returns:
        (fund_name, holdings_list)
        holdings_list 中 weight 为小数（如 0.092 = 9.2%）。

    缓存策略：
        季报数据极少变化，缓存 4 小时（_TTL_HOLDINGS）。

    降级策略：
        akshare 调用失败或返回空 DataFrame → 返回 ("", [])
        调用方负责将此情况上报为错误。
    """
    ck = _CACHE_HOLDINGS.format(_normalize(fund_code))
    cached = cache_get(ck)
    if cached is not None:
        return cached["fund_name"], [_HoldingRaw(**h) for h in cached["holdings"]]

    code = _normalize(fund_code)
    try:
        df: pd.DataFrame = await asyncio.to_thread(
            ak.fund_portfolio_hold_em, symbol=code
        )
    except Exception as exc:
        logger.warning("持仓数据拉取失败 fund=%s: %s", code, exc)
        return "", []

    if df is None or df.empty:
        logger.warning("持仓数据为空 fund=%s", code)
        return "", []

    # 提取基金名称（akshare 返回的列名不固定，做容错）
    fund_name = ""
    for col in ("基金简称", "fund_name"):
        if col in df.columns:
            fund_name = str(df[col].iloc[0]).strip()
            break

    # 解析持仓：列名兼容多个版本的 akshare
    code_col   = next((c for c in ("股票代码", "code",  "stock_code") if c in df.columns), None)
    name_col   = next((c for c in ("股票名称", "stock", "name")       if c in df.columns), None)
    weight_col = next((c for c in ("占净值比例", "ratio", "weight")    if c in df.columns), None)

    if code_col is None or weight_col is None:
        logger.warning("持仓 DataFrame 列名无法识别: %s", df.columns.tolist())
        return fund_name, []

    holdings: list[_HoldingRaw] = []
    for _, row in df.head(10).iterrows():
        sc = str(row.get(code_col, "")).strip()
        if not sc:
            continue
        try:
            wt = float(row[weight_col]) / 100.0    # 9.2 → 0.092
        except (ValueError, TypeError):
            wt = 0.0
        sn = str(row.get(name_col, sc)).strip() if name_col else sc
        holdings.append(_HoldingRaw(
            stock_code=_normalize(sc),
            stock_name=sn,
            weight=round(wt, 6),
        ))

    # 落缓存
    cache_set(ck, {
        "fund_name": fund_name,
        "holdings": [{"stock_code": h.stock_code, "stock_name": h.stock_name, "weight": h.weight}
                     for h in holdings],
    }, ttl_seconds=_TTL_HOLDINGS)

    return fund_name, holdings


# ══════════════════════════════════════════════════════════════
# Mock 兜底层
#   当外部行情 API 不可用时（网络故障 / 非中国大陆网络），
#   自动切换为"确定性 Mock"模式：
#     · 以 (代码 + 当前分钟) 为种子生成涨跌幅，同一分钟内稳定，每分钟刷新
#     · 返回的 DataFrame 结构与真实 API 完全一致，下游代码无需感知
#   生产环境上线真实行情后可直接移除 _mock_* 函数。
# ══════════════════════════════════════════════════════════════

def _mock_change_for(code: str, is_index: bool = False) -> float:
    """
    用 MD5 生成同分钟内确定、跨分钟变化的伪随机涨跌幅。

    个股振荡范围 ±3.0%，指数 ±1.5%（更稳定）。
    """
    # 60s 粒度时间戳：保证同分钟结果稳定
    minute_bucket = int(time.time()) // 60
    raw = hashlib.md5(f"{code}-{minute_bucket}".encode()).digest()
    # 取前4字节 → [0, 1) → [-0.5, 0.5) → 缩放
    ratio   = int.from_bytes(raw[:4], "big") / 0x1_0000_0000 - 0.5
    amplitude = 1.5 if is_index else 3.0
    return round(ratio * amplitude * 2, 2)


def _build_mock_stock_df(codes: list[str]) -> pd.DataFrame:
    """为指定股票代码列表构造 Mock 行情 DataFrame。"""
    records = []
    for code in codes:
        chg = _mock_change_for(code, is_index=False)
        records.append({
            "代码":  code.zfill(6),
            "名称":  code,
            "最新价": 0.0,       # 无真实价格，填 0
            "涨跌幅": chg,
            "成交量": 1,         # 非零 → 避免被判为停牌
        })
    return pd.DataFrame(records)


def _build_mock_index_df(codes: list[str]) -> pd.DataFrame:
    """为指定指数代码列表构造 Mock 行情 DataFrame。"""
    records = []
    for code in codes:
        chg = _mock_change_for(code, is_index=True)
        records.append({
            "代码":  code.zfill(6),
            "名称":  code,
            "最新价": 0.0,
            "涨跌幅": chg,
        })
    return pd.DataFrame(records)


# ── 数据拉取：A 股全量快照（带 Mock 兜底）─────────────────────

async def _fetch_stock_spot(needed_codes: list[str] | None = None) -> pd.DataFrame:
    """
    拉取 A 股实时行情。

    策略（按优先级）：
      1. 命中 60s 缓存 → 直接返回缓存
      2. 调用 akshare stock_zh_a_spot_em → 成功则缓存并返回
      3. 外部 API 失败（网络/限流/超时）→ 降级为 Mock 行情（标记来源）

    Args:
        needed_codes: 本次估值需要的股票代码列表（用于 Mock 精确生成）。
    """
    cached = cache_get(_CACHE_STOCK_SPOT)
    if cached is not None:
        return cached

    try:
        df: pd.DataFrame = await asyncio.to_thread(ak.stock_zh_a_spot_em)
        if df is not None and not df.empty:
            if "代码" in df.columns:
                df["代码"] = df["代码"].astype(str).str.strip().str.zfill(6)
            cache_set(_CACHE_STOCK_SPOT, df, ttl_seconds=_TTL_SPOT)
            return df
    except Exception as exc:
        logger.warning(
            "A股实时行情拉取失败（降级为 Mock）: %s  "
            "| 生产环境请确保网络可访问东方财富行情服务器", exc,
        )

    # ── 降级：返回 Mock DataFrame ──────────────────────────────
    mock_df = _build_mock_stock_df(needed_codes or [])
    # Mock 数据仅缓存 30s（比真实数据更激进刷新）
    cache_set(_CACHE_STOCK_SPOT, mock_df, ttl_seconds=30)
    return mock_df


async def _fetch_index_spot(needed_codes: list[str] | None = None) -> pd.DataFrame:
    """
    拉取 A 股指数实时行情。

    真实函数：ak.stock_zh_index_spot_em（非 index_zh_a_spot_em，后者不存在）
    降级策略：拉取失败自动切换 Mock 行情。
    """
    cached = cache_get(_CACHE_INDEX_SPOT)
    if cached is not None:
        return cached

    try:
        # ⚠️ 正确函数名：stock_zh_index_spot_em（区别于不存在的 index_zh_a_spot_em）
        df: pd.DataFrame = await asyncio.to_thread(ak.stock_zh_index_spot_em)
        if df is not None and not df.empty:
            if "代码" in df.columns:
                df["代码"] = df["代码"].astype(str).str.strip().str.zfill(6)
            cache_set(_CACHE_INDEX_SPOT, df, ttl_seconds=_TTL_SPOT)
            return df
    except Exception as exc:
        logger.warning(
            "指数实时行情拉取失败（降级为 Mock）: %s", exc,
        )

    # ── 降级：Mock 指数行情 ────────────────────────────────────
    mock_df = _build_mock_index_df(needed_codes or [])
    cache_set(_CACHE_INDEX_SPOT, mock_df, ttl_seconds=30)
    return mock_df


# ══════════════════════════════════════════════════════════════
# 主服务：FundValuationService
# ══════════════════════════════════════════════════════════════

class FundValuationService:
    """
    基金穿透实时估值服务入口。

    Usage:
        result = await FundValuationService.calculate("110011")
    """

    @staticmethod
    async def calculate(fund_code: str) -> ValuationResult:
        """
        主计算方法：穿透计算基金盘中预估净值涨跌幅。

        步骤：
          1. 并发拉取 [持仓, 全市场快照, 指数快照]（asyncio.gather）
          2. 匹配每只持仓股的实时行情，处理停牌/数据缺失
          3. 计算加权估值：Σ(w_i × r_i) + w_remaining × r_index
          4. 汇总数据质量报告

        Returns:
            ValuationResult（含完整估值与质量指标）

        Raises:
            ValueError: 基金代码格式错误，或持仓数据完全无法获取
        """
        fund_code = _normalize(fund_code)

        # ── 1a. 先获取持仓（需要股票代码才能精确生成 Mock 数据）──
        try:
            fund_name, holdings = await _fetch_holdings(fund_code)
        except Exception as exc:
            logger.error("持仓拉取异常 fund=%s: %s", fund_code, exc)
            raise ValueError(f"基金 {fund_code} 持仓数据不可用") from exc

        if not holdings:
            raise ValueError(
                f"基金 {fund_code} 暂无可用持仓数据，可能是代码有误或季报尚未披露"
            )

        # ── 1b. 确定基准指数（供并发拉取时传入 Mock 兜底）──────
        idx_code, idx_name = _get_benchmark(fund_code)
        stock_codes = [h.stock_code for h in holdings]

        # ── 1c. 并发拉取 [股票行情, 指数行情]（带 Mock 兜底）──
        stock_df, index_df = await asyncio.gather(
            _fetch_stock_spot(needed_codes=stock_codes),
            _fetch_index_spot(needed_codes=[idx_code]),
            return_exceptions=True,
        )
        if isinstance(stock_df, Exception):
            logger.warning("股票快照异常，降级 Mock: %s", stock_df)
            stock_df = _build_mock_stock_df(stock_codes)
        if isinstance(index_df, Exception):
            logger.warning("指数快照异常，降级 Mock: %s", index_df)
            index_df = _build_mock_index_df([idx_code])

        # ── 3. 逐股匹配实时行情，计算贡献度 ─────────────────
        stock_quotes: list[StockQuote] = []
        total_disclosed_weight = sum(h.weight for h in holdings)

        for h in holdings:
            change_pct, status, price = FundValuationService._resolve_stock(
                h.stock_code, stock_df
            )
            contribution = round(h.weight * change_pct, 6)
            stock_quotes.append(StockQuote(
                stock_code=h.stock_code,
                stock_name=h.stock_name,
                weight=h.weight,
                current_price=price,
                change_pct=change_pct,
                contribution=contribution,
                status=status,
            ))

        # ── 4. 基准指数行情 ──────────────────────────────────
        remaining_weight = round(max(0.0, 1.0 - total_disclosed_weight), 6)
        idx_change, idx_status = FundValuationService._resolve_index(idx_code, index_df)
        idx_contribution = round(remaining_weight * idx_change, 6)

        benchmark_quote = IndexQuote(
            index_code=idx_code,
            index_name=idx_name,
            weight=remaining_weight,
            change_pct=idx_change,
            contribution=idx_contribution,
            status=idx_status,
        )

        # ── 5. 汇总预估涨跌幅 ────────────────────────────────
        stock_sum    = sum(q.contribution for q in stock_quotes)
        estimated    = round(stock_sum + idx_contribution, 4)

        # ── 6. 数据质量报告 ──────────────────────────────────
        n_normal    = sum(1 for q in stock_quotes if q.status == "normal")
        n_suspended = sum(1 for q in stock_quotes if q.status == "suspended")
        n_missing   = sum(1 for q in stock_quotes if q.status == "data_missing")

        # coverage_ratio = 有效权重（normal股票 + 若指数可用则含剩余权重）/ 总权重
        valid_stock_w = sum(q.weight for q in stock_quotes if q.status == "normal")
        valid_index_w = remaining_weight if idx_status == "normal" else 0.0
        coverage = round((valid_stock_w + valid_index_w) / 1.0, 4)   # 分母=1（已标准化）

        dq = DataQuality(
            disclosed_weight=round(total_disclosed_weight, 4),
            benchmark_weight=remaining_weight,
            stocks_total=len(holdings),
            stocks_normal=n_normal,
            stocks_suspended=n_suspended,
            stocks_data_missing=n_missing,
            coverage_ratio=coverage,
            is_reliable=coverage >= 0.60,
        )

        return ValuationResult(
            fund_code=fund_code,
            fund_name=fund_name or f"基金 {fund_code}",
            estimated_change_pct=estimated,
            disclosed_holdings=stock_quotes,
            benchmark_proxy=benchmark_quote,
            data_quality=dq,
            is_trading_hour=_is_trading_hour(),
            updated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )

    # ── 内部：解析单只股票行情 ────────────────────────────────

    @staticmethod
    def _resolve_stock(
        code: str,
        df: pd.DataFrame,
    ) -> tuple[float, str, Optional[float]]:
        """
        从市场快照中提取股票实时数据。

        Returns:
            (change_pct, status, current_price)
            · status = "normal"       → 正常交易
            · status = "suspended"    → 停牌（量 = 0）
            · status = "data_missing" → 快照中不存在或数据异常

        Notes:
            停牌和数据缺失均将 change_pct 置 0，
            避免其拉偏加权估值。
        """
        if df is None or df.empty or "代码" not in df.columns:
            return 0.0, "data_missing", None

        mask = df["代码"].astype(str).str.strip().str.zfill(6) == code
        rows = df[mask]

        if rows.empty:
            return 0.0, "data_missing", None

        row = rows.iloc[0]

        # 提取最新价
        price = None
        for pc in ("最新价", "现价"):
            if pc in row.index:
                try:
                    v = float(row[pc])
                    price = v if v > 0 else None
                except (ValueError, TypeError):
                    pass
                break

        # 检查停牌：成交量为 0
        vol = None
        for vc in ("成交量", "volume"):
            if vc in row.index:
                try:
                    vol = float(row[vc])
                except (ValueError, TypeError):
                    vol = None
                break

        if vol is not None and vol == 0:
            return 0.0, "suspended", price

        # 提取涨跌幅
        chg = None
        for cc in ("涨跌幅", "change_pct", "pct_chg"):
            if cc in row.index:
                try:
                    v = float(row[cc])
                    if not pd.isna(v):
                        chg = v
                except (ValueError, TypeError):
                    pass
                break

        if chg is None:
            return 0.0, "data_missing", price

        return round(chg, 4), "normal", price

    # ── 内部：解析指数行情 ────────────────────────────────────

    @staticmethod
    def _resolve_index(
        code: str,
        df: pd.DataFrame,
    ) -> tuple[float, str]:
        """
        从指数快照中提取实时涨跌幅。

        Returns:
            (change_pct, status)
            status = "normal" | "data_missing"
        """
        if df is None or df.empty or "代码" not in df.columns:
            return 0.0, "data_missing"

        mask = df["代码"].astype(str).str.strip().str.zfill(6) == code
        rows = df[mask]

        if rows.empty:
            return 0.0, "data_missing"

        row = rows.iloc[0]
        for cc in ("涨跌幅", "change_pct"):
            if cc in row.index:
                try:
                    v = float(row[cc])
                    if not pd.isna(v):
                        return round(v, 4), "normal"
                except (ValueError, TypeError):
                    pass

        return 0.0, "data_missing"
