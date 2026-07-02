"""市场扫描服务 — 基于 akshare 真实数据"""
import asyncio
import logging
from ..models.schemas import MarketOverview, IndexValuation
from ..data_fetch.fund_data import FundDataFetcher

logger = logging.getLogger(__name__)


class MarketScanService:
    """市场机会扫描与估值分析"""

    @staticmethod
    async def get_market_overview() -> MarketOverview:
        """市场概览：主要指数估值、股债性价比、北向资金"""
        try:
            # 用主要指数代码拉取估值
            main_indices = ["000300", "000905", "399006", "000688", "000001"]
            index_names = {"000300": "沪深300", "000905": "中证500", "399006": "创业板指",
                           "000688": "科创50", "000001": "上证指数"}

            index_data = []
            raw_results = await asyncio.gather(*[FundDataFetcher.fetch_index_valuation(idx) for idx in main_indices])

            for idx_code, raw in zip(main_indices, raw_results):
                if raw and raw.get("pe"):
                    index_data.append(IndexValuation(
                        index_name=raw.get("index_name", index_names.get(idx_code, idx_code)),
                        index_code=idx_code,
                        pe=raw.get("pe", 0),
                        pe_percentile=raw.get("pe_percentile", 50),
                        pb=raw.get("pb", 0),
                        pb_percentile=raw.get("pb_percentile", 50),
                        yield_ratio=raw.get("yield_ratio", 0),
                    ))

            # 如果全没拉到，回退 mock
            if not index_data:
                raise RuntimeError("all index fetches failed")

            # 北向资金
            nf = await FundDataFetcher.fetch_north_flow(1)
            north_flow = float(nf[0]["value"]) if nf else 0

            avg_pe = sum(i.pe_percentile for i in index_data) / len(index_data)

            return MarketOverview(
                indices=index_data,
                stock_bond_ratio=round(avg_pe / 30, 2),  # 近似股债性价比
                north_flow=north_flow,
                avg_pe_percentile=round(avg_pe, 1),
            )
        except Exception as e:
            logger.warning(f"市场概览接口失败，回落 mock: {e}")
            return await MarketScanService._mock_overview()

    @staticmethod
    async def _mock_overview() -> MarketOverview:
        """mock 数据兜底"""
        indices = [
            IndexValuation(index_name="沪深300", index_code="000300", pe=12.5, pe_percentile=35, pb=1.4, pb_percentile=28, yield_ratio=2.8),
            IndexValuation(index_name="中证500", index_code="000905", pe=18.2, pe_percentile=22, pb=1.8, pb_percentile=18, yield_ratio=1.9),
            IndexValuation(index_name="创业板指", index_code="399006", pe=28.5, pe_percentile=15, pb=3.8, pb_percentile=12, yield_ratio=1.1),
        ]
        return MarketOverview(indices=indices, stock_bond_ratio=1.8, north_flow=35.6, avg_pe_percentile=24.0)

    @staticmethod
    async def get_hot_sectors() -> list[dict]:
        """获取热门行业板块涨跌"""
        return await FundDataFetcher.fetch_sector_performance()

    @staticmethod
    async def get_undervalued_indices() -> list[dict]:
        """低估指数推荐：找出 PE 百分位最低的指数"""
        try:
            raw = await FundDataFetcher.fetch_index_valuations()
            valid = [r for r in raw if r.get("pe_percentile", 100) > 0]
            valid.sort(key=lambda x: x["pe_percentile"])
            result = []
            for r in valid[:5]:
                pct = r["pe_percentile"]
                if pct <= 10:
                    reason = f"PE 处于近5年最低 {pct:.0f}% 分位，显著低估"
                elif pct <= 30:
                    reason = f"PE 处于近5年较低 {pct:.0f}% 分位，关注布局机会"
                else:
                    reason = f"PE 处于 {pct:.0f}% 分位"
                result.append({
                    "index": r.get("index_name", ""),
                    "code": r.get("index_code", ""),
                    "pe_percentile": pct,
                    "reason": reason,
                })
            return result
        except Exception as e:
            logger.warning(f"获取低估指数失败: {e}")
            return []

    @staticmethod
    async def get_north_flow() -> list[dict]:
        """北向资金流向（近 20 日）"""
        try:
            data = await FundDataFetcher.fetch_north_flow(20)
            return data if data else []
        except Exception as e:
            logger.warning(f"获取北向资金失败: {e}")
            return []
