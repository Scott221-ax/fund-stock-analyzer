"""外部基金/市场数据采集 -- 基于 akshare 真实数据"""
import asyncio
import logging
from datetime import date, datetime
from typing import Optional

import hashlib
import akshare as ak
from ..util_cache import get as cache_get, set as cache_set

logger = logging.getLogger(__name__)


def _cache_key(prefix: str, *args) -> str:
    raw = f"{prefix}:{chr(58).join(str(a) for a in args)}"
    return hashlib.md5(raw.encode()).hexdigest()


class FundDataFetcher:
    """基金数据采集器（从公开数据源拉取）"""

    # 股票代码 → 申万行业映射（覆盖常见重仓股）
    SECTOR_MAP = {
        # 食品饮料
        "600519": "食品饮料", "000858": "食品饮料", "000568": "食品饮料",
        "600809": "食品饮料", "600887": "食品饮料", "603288": "食品饮料",
        "002304": "食品饮料", "000596": "食品饮料", "600132": "食品饮料",
        # 医药生物
        "300760": "医药生物", "600276": "医药生物", "603259": "医药生物",
        "000661": "医药生物", "300015": "医药生物", "002007": "医药生物",
        "688981": "医药生物", "300122": "医药生物", "000963": "医药生物",
        # 电力设备/新能源
        "300750": "电力设备", "002594": "汽车", "605117": "电力设备",
        "300274": "电力设备", "300124": "电力设备", "601012": "电力设备",
        "688599": "电力设备", "002459": "电力设备", "688005": "电力设备",
        # 电子/半导体
        "002415": "电子", "600745": "电子", "002475": "电子",
        "688981": "电子", "002371": "电子", "300782": "电子",
        "603501": "电子", "688012": "电子", "600703": "电子",
        # 银行
        "600036": "银行", "601166": "银行", "000001": "银行",
        "600000": "银行", "601398": "银行", "601939": "银行",
        "002142": "银行", "600016": "银行",
        # 非银金融
        "601318": "非银金融", "600030": "非银金融", "601628": "非银金融",
        "601211": "非银金融", "600837": "非银金融", "002736": "非银金融",
        # 煤炭
        "601225": "煤炭", "601088": "煤炭", "600188": "煤炭",
        "600985": "煤炭", "601898": "煤炭", "600546": "煤炭",
        # 石油石化
        "00883": "石油石化", "600028": "石油石化", "601857": "石油石化",
        "600346": "石油石化", "002493": "石油石化",
        # 汽车
        "600741": "汽车", "000625": "汽车", "601238": "汽车",
        "600104": "汽车", "002920": "汽车",
        # 家用电器
        "000333": "家用电器", "000651": "家用电器", "002242": "家用电器",
        # 通信/计算机
        "000063": "通信", "600941": "通信", "300308": "通信",
        "002230": "计算机", "688111": "计算机", "600570": "计算机",
        "300033": "计算机", "002410": "计算机",
        # 国防军工
        "600760": "国防军工", "600893": "国防军工", "002179": "国防军工",
        "600862": "国防军工", "600765": "国防军工",
        # 有色金属
        "601899": "有色金属", "600547": "有色金属", "000630": "有色金属",
        "002466": "有色金属", "600489": "有色金属",
        # 房地产
        "001979": "房地产", "600048": "房地产", "000002": "房地产",
        # 建筑装饰
        "601668": "建筑装饰", "601390": "建筑装饰", "601186": "建筑装饰",
        "601800": "建筑装饰",
        # 交通运输
        "601111": "交通运输", "600029": "交通运输", "601006": "交通运输",
        # 公用事业
        "600900": "公用事业", "600886": "公用事业", "601985": "公用事业",
        "600795": "公用事业", "600011": "公用事业",
        # 农林牧渔
        "002714": "农林牧渔", "300498": "农林牧渔", "600873": "农林牧渔",
        # 基础化工
        "600309": "基础化工", "601216": "基础化工", "002601": "基础化工",
        "600426": "基础化工", "600989": "基础化工",
    }

    @staticmethod
    def lookup_sector(stock_code: str, stock_name: str = "") -> str:
        """根据股票代码查找行业，未知股票标记为其他"""
        if not stock_code:
            return "其他"
        code = stock_code.strip().lstrip("0")  # 去前导零
        # 先查完整代码
        if stock_code.strip() in FundDataFetcher.SECTOR_MAP:
            return FundDataFetcher.SECTOR_MAP[stock_code.strip()]
        # 再去零再查
        if code in FundDataFetcher.SECTOR_MAP:
            return FundDataFetcher.SECTOR_MAP[code]
        # 港股：代码带 .HK 后缀
        hk_code = stock_code.strip().replace(".HK", "")
        if hk_code in FundDataFetcher.SECTOR_MAP:
            return FundDataFetcher.SECTOR_MAP[hk_code]
        return "其他"

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
        ck = _cache_key("nav", code)
        if start_date is None and end_date is None:
            cached = cache_get(ck)
            if cached is not None:
                return cached
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
        ck = _cache_key("f_info", code)
        cached = cache_get(ck)
        if cached is not None:
            return cached
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
        ck = _cache_key("idx_val", index_code)
        cached = cache_get(ck)
        if cached is not None:
            return cached
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
        ck = _cache_key("f_pos", code)
        cached = cache_get(ck)
        if cached is not None:
            return cached
        code = FundDataFetcher._normalize_code(code)
        try:
            df = await asyncio.to_thread(ak.fund_portfolio_hold_em, symbol=code)
            if df is None or df.empty:
                return []
            df = df.rename(columns={"股票名称": "stock", "占净值比例": "ratio", "股票代码": "stock_code"})
            result = df[["stock_code", "stock", "ratio"]].head(10).to_dict(orient="records")
            cache_set(ck, result, ttl_seconds=86400)
            return result
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
    async def fetch_us_stock_data(code: str, start_date=None, end_date=None) -> list[dict]:
        """获取美股/ETF 历史行情（yfinance）"""
        import yfinance as yf
        try:
            s = start_date.strftime("%Y-%m-%d") if start_date else None
            e = end_date.strftime("%Y-%m-%d") if end_date else None
            kwargs = {"tickers": code, "auto_adjust": True, "progress": False, "multi_level_index": False}
            if s: kwargs["start"] = s
            if e: kwargs["end"] = e
            df = await asyncio.to_thread(lambda: yf.download(**kwargs))
            if df is None or df.empty:
                return []
            df = df.reset_index()
            df.columns = [str(c).split(",")[0].strip() for c in df.columns]
            rename = {}
            for c in df.columns:
                if "date" in c.lower(): rename[c] = "date"
                elif "close" in c.lower(): rename[c] = "price"
            df = df.rename(columns=rename)
            if "date" in df.columns:
                df["date"] = df["date"].astype(str).str[:10]
            result_cols = [c for c in ["date", "price"] if c in df.columns]
            return df[result_cols].to_dict(orient="records") if result_cols else []
        except Exception as ex:
            logger.warning(f"获取美股 {code} 数据失败: {ex}")
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
