"""外部基金/市场数据采集 -- 基于 akshare 真实数据"""
import asyncio
import logging
from datetime import date, datetime
from typing import Optional

import akshare as ak

logger = logging.getLogger(__name__)


class FundDataFetcher:
    """基金数据采集器（从公开数据源拉取）"""

    INDEX_NAMES = {
        "000300": "沪深300", "000905": "中证500", "399006": "创业板指",
        "000688": "科创50", "000001": "上证指数", "399001": "深证成指",
        "000016": "上证50", "000852": "中证1000",
    }

    @staticmethod
    def _normalize_code(code: str) -> str:
        code = code.strip().replace(".SZ", "").replace(".SH", "").replace(".OF", "")
        return code.zfill(6)

    @staticmethod
    async def fetch_fund_nav(code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> list[dict]:
        """获取基金历史净值"""
        code = FundDataFetcher._normalize_code(code)
        try:
            s = start_date.strftime("%Y%m%d") if start_date else "20000101"
            e = end_date.strftime("%Y%m%d") if end_date else datetime.now().strftime("%Y%m%d")
            df = await asyncio.to_thread(ak.fund_etf_hist_em, symbol=code, period="daily", start_date=s, end_date=e, adjust="")
            if df is None or df.empty:
                return []
            df = df.rename(columns={"净值日期": "date", "单位净值": "nav", "累计净值": "acc_nav"})
            df["date"] = df["date"].astype(str)
            return df[["date", "nav", "acc_nav"]].to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取 {code} 净值失败: {e}")
            return []

    @staticmethod
    async def fetch_latest_nav(code: str) -> Optional[float]:
        """获取基金最新净值"""
        navs = await FundDataFetcher.fetch_fund_nav(code)
        if navs:
            return float(navs[-1]["nav"])
        return None

    @staticmethod
    async def fetch_fund_info(code: str) -> dict:
        """获取基金基本信息"""
        code = FundDataFetcher._normalize_code(code)
        try:
            df = await asyncio.to_thread(ak.fund_name_em)
            if df is None or df.empty:
                return {}
            code_raw = code.lstrip("0")
            mask = df["基金代码"].astype(str).str.strip().apply(lambda x: x.lstrip("0") == code_raw)
            row = df[mask]
            if row.empty:
                return {}
            r = row.iloc[0]
            return {
                "code": str(r["基金代码"]).strip(),
                "name": str(r["基金简称"]).strip(),
                "type": str(r.get("基金类型", "")).strip(),
                "company": "",
            }
        except Exception as e:
            logger.warning(f"获取 {code} 信息失败: {e}")
            return {}

    @staticmethod
    async def fetch_index_valuation(index_code: str) -> dict:
        """获取指数估值（PE + 历史百分位 + 股息率）"""
        try:
            idx_name = FundDataFetcher.INDEX_NAMES.get(index_code, index_code)
            # 从历史数据获取滚动市盈率
            hist = await asyncio.to_thread(
                ak.stock_zh_index_hist_csindex, symbol=index_code,
                start_date="20210101", end_date="20260701",
            )
            if hist is None or hist.empty or "滚动市盈率" not in hist.columns:
                return {}

            current_pe = float(hist["滚动市盈率"].iloc[-1] or 0)
            pes = hist["滚动市盈率"].dropna().values
            pe_percentile = 50.0
            if len(pes) > 20 and current_pe > 0:
                pe_percentile = round(float((pes <= current_pe).sum() / len(pes) * 100), 1)

            real_name = str(hist["指数中文简称"].iloc[-1]) if "指数中文简称" in hist.columns else ""

            # 从估值表获取股息率
            yield_ratio = 0
            try:
                df_val = await asyncio.to_thread(ak.stock_zh_index_value_csindex)
                if df_val is not None and not df_val.empty:
                    code_raw = index_code.strip().lstrip("0")
                    val_mask = df_val["指数代码"].astype(str).str.strip().apply(
                        lambda x: x.lstrip("0") == code_raw or x.strip() == index_code)
                    val_row = df_val[val_mask]
                    if not val_row.empty:
                        yield_ratio = float(val_row.iloc[0].get("股息率1", 0) or 0)
            except Exception:
                pass

            return {
                "index_code": index_code,
                "index_name": real_name or idx_name,
                "pe": round(current_pe, 2),
                "pe_percentile": pe_percentile,
                "pb": 0, "pb_percentile": 0,
                "yield_ratio": round(yield_ratio, 2),
            }
        except Exception as e:
            logger.warning(f"获取指数 {index_code} 估值失败: {e}")
            return {}

    @staticmethod
    async def fetch_fund_position(code: str) -> list[dict]:
        """获取基金前十大重仓股"""
        code = FundDataFetcher._normalize_code(code)
        try:
            df = await asyncio.to_thread(ak.fund_portfolio_hold_em, symbol=code)
            if df is None or df.empty:
                return []
            df = df.rename(columns={"股票名称": "stock", "占净值比例": "ratio"})
            return df[["stock", "ratio"]].head(10).to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取 {code} 持仓失败: {e}")
            return []

    @staticmethod
    async def search_funds(keyword: str) -> list[dict]:
        """搜索基金（代码或名称模糊匹配）"""
        if not keyword.strip():
            return []
        try:
            df = await asyncio.to_thread(ak.fund_name_em)
            if df is None or df.empty:
                return []
            mask = (
                df["基金代码"].astype(str).str.contains(keyword, na=False) |
                df["基金简称"].astype(str).str.contains(keyword, na=False)
            )
            result = df[mask].head(20)
            return result[["基金代码", "基金简称", "基金类型"]].rename(
                columns={"基金代码": "code", "基金简称": "name", "基金类型": "type"}
            ).to_dict(orient="records")
        except Exception as e:
            logger.warning(f"搜索基金失败: {e}")
            return []

    @staticmethod
    async def fetch_fund_rank() -> list[dict]:
        """获取基金收益排名"""
        try:
            df = await asyncio.to_thread(ak.fund_rank, type="raise")
            if df is None or df.empty:
                return []
            df = df.rename(columns={
                "基金代码": "code", "基金简称": "name",
                "单位净值": "nav", "近1年收益率": "return_1y",
            })
            return df[["code", "name", "nav", "return_1y"]].head(50).to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取基金排名失败: {e}")
            return []

    @staticmethod
    async def fetch_north_flow(days: int = 10) -> list[dict]:
        """北向资金流向（过滤 NaN 无效值）"""
        try:
            df = await asyncio.to_thread(ak.stock_hsgt_hist_em)
            if df is None or df.empty:
                return []
            df = df.rename(columns={"日期": "date", "当日成交净买额": "value"})
            df["date"] = df["date"].astype(str)
            df["value"] = df["value"].fillna(0).astype(float)
            # 过滤 0 值（当日数据未更新），取最近有数据的 days 条
            valid = df[df["value"] != 0]
            if len(valid) == 0:
                return df.tail(days)[["date", "value"]].to_dict(orient="records")
            return valid.tail(days)[["date", "value"]].to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取北向资金失败: {e}")
            return []

    @staticmethod
    async def fetch_sector_performance() -> list[dict]:
        """获取行业板块涨跌"""
        try:
            df = await asyncio.to_thread(ak.stock_board_industry_name_em)
            if df is None or df.empty:
                return []
            df = df.rename(columns={"板块名称": "sector", "涨跌幅": "change_pct"})
            df = df.sort_values("change_pct", ascending=False).head(10)
            def _mom(v):
                if v > 2: return "strong"
                if v > 0: return "moderate"
                if v > -2: return "weak"
                return "danger"
            result = []
            for _, r in df.iterrows():
                result.append({
                    "sector": r["sector"],
                    "change_pct": round(float(r["change_pct"]), 2),
                    "momentum": _mom(float(r["change_pct"])),
                })
            return result
        except Exception as e:
            logger.warning(f"获取行业板块失败: {e}")
            return []
