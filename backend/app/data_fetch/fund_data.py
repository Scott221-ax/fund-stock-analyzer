"""外部基金/市场数据采集"""
from datetime import date
from typing import Optional


class FundDataFetcher:
    """基金数据采集器（从公开数据源拉取）"""

    @staticmethod
    async def fetch_fund_nav(code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> list[dict]:
        """
        获取基金历史净值
        数据源：天天基金 / akshare
        当前返回 mock 数据
        """
        # TODO: 使用 akshare.fund_etf_hist_em() 或类似接口
        if start_date is None:
            start_date = date(2025, 1, 1)
        if end_date is None:
            end_date = date.today()

        # mock 数据示例
        return [
            {"date": "2026-06-01", "nav": 2.45, "acc_nav": 2.85},
            {"date": "2026-06-15", "nav": 2.52, "acc_nav": 2.92},
            {"date": "2026-06-30", "nav": 2.48, "acc_nav": 2.88},
        ]

    @staticmethod
    async def fetch_index_valuation(index_code: str) -> dict:
        """
        获取指数估值（PE/PB/股息率）
        数据源：中证指数官网 / akshare
        """
        # TODO: 使用 akshare.stock_zh_index_valuation()
        return {
            "index_code": index_code,
            "pe": 12.5,
            "pe_percentile": 35.0,
            "pb": 1.4,
            "pb_percentile": 28.0,
            "yield_ratio": 2.8,
        }

    @staticmethod
    async def fetch_fund_position(code: str) -> list[dict]:
        """
        获取基金持仓（前十大重仓股）
        数据源：天天基金季报 / akshare
        """
        # TODO: 使用 akshare.fund_portfolio_hold()
        return [
            {"stock": "贵州茅台", "ratio": 9.8},
            {"stock": "宁德时代", "ratio": 8.5},
            {"stock": "腾讯控股", "ratio": 7.2},
            {"stock": "招商银行", "ratio": 5.6},
            {"stock": "中国平安", "ratio": 4.3},
        ]
