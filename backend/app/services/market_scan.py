"""市场扫描服务"""
from ..models.schemas import MarketOverview, IndexValuation


class MarketScanService:
    """市场机会扫描与估值分析"""

    @staticmethod
    async def get_market_overview() -> MarketOverview:
        """市场概览：主要指数估值、股债性价比等"""
        # TODO: 接入真实数据（akshare）
        indices = [
            IndexValuation(index_name="沪深300", index_code="000300", pe=12.5, pe_percentile=35, pb=1.4, pb_percentile=28, yield_ratio=2.8),
            IndexValuation(index_name="中证500", index_code="000905", pe=18.2, pe_percentile=22, pb=1.8, pb_percentile=18, yield_ratio=1.9),
            IndexValuation(index_name="创业板指", index_code="399006", pe=28.5, pe_percentile=15, pb=3.8, pb_percentile=12, yield_ratio=1.1),
            IndexValuation(index_name="恒生指数", index_code="HSI", pe=9.8, pe_percentile=20, pb=1.1, pb_percentile=15, yield_ratio=3.8),
            IndexValuation(index_name="标普500", index_code="SPX", pe=22.0, pe_percentile=72, pb=4.5, pb_percentile=68, yield_ratio=1.5),
        ]
        return MarketOverview(
            indices=indices,
            stock_bond_ratio=1.8,
            north_flow=35.6,
            avg_pe_percentile=sum(i.pe_percentile for i in indices) / len(indices),
        )

    @staticmethod
    async def get_hot_sectors() -> list[dict]:
        """热门行业板块"""
        return [
            {"sector": "AI / 人工智能", "change_pct": 4.2, "momentum": "strong"},
            {"sector": "半导体", "change_pct": 3.5, "momentum": "strong"},
            {"sector": "新能源汽车", "change_pct": 1.8, "momentum": "moderate"},
            {"sector": "医药", "change_pct": -0.5, "momentum": "weak"},
            {"sector": "消费", "change_pct": 0.2, "momentum": "moderate"},
        ]

    @staticmethod
    async def get_undervalued_indices() -> list[dict]:
        """低估指数推荐（PE/PB 历史低位）"""
        return [
            {"index": "中证医疗", "code": "399989", "pe_percentile": 5, "reason": "PE处于近5年最低5%分位"},
            {"index": "中证新能源", "code": "399808", "pe_percentile": 8, "reason": "PE处于近5年最低8%分位"},
            {"index": "中证500", "code": "000905", "pe_percentile": 22, "reason": "PE处于近5年较低分位"},
        ]

    @staticmethod
    async def get_north_flow() -> list[dict]:
        """北向资金流向"""
        # TODO: 接入真实数据
        return [
            {"date": "2026-06-30", "value": 35.6},
            {"date": "2026-06-29", "value": -12.3},
            {"date": "2026-06-26", "value": 48.2},
            {"date": "2026-06-25", "value": 22.8},
            {"date": "2026-06-24", "value": -5.6},
        ]
