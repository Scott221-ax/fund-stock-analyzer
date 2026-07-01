from datetime import date
import asyncio
import logging
from ..models.schemas import FundEvalResult
from ..data_fetch.fund_data import FundDataFetcher

logger = logging.getLogger(__name__)


class FundEvalService:
    """单只基金的评分与诊断"""

    @staticmethod
    async def evaluate(code: str) -> FundEvalResult:
        """综合评价一只基金"""
        try:
            info = await FundDataFetcher.fetch_fund_info(code)
            name = info.get("name", "")

            # 获取排名数据，估算同类排名
            rank = 50
            score = 60
            try:
                rank_data = await FundDataFetcher.fetch_fund_rank()
                codes_in_rank = [r["code"] for r in rank_data]
                if code in codes_in_rank:
                    pos = codes_in_rank.index(code)
                    rank = round(pos / len(codes_in_rank) * 100, 1)
                    score = round(80 - rank * 0.5, 1)
            except Exception:
                pass

            # 估算风险等级（基于净值波动）
            risk_level = "中"
            navs = await FundDataFetcher.fetch_fund_nav(code, start_date=date(2025, 1, 1))
            if navs and len(navs) > 5:
                prices = [float(n["nav"]) for n in navs if n.get("nav")]
                if prices:
                    import numpy as np
                    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                    volatility = np.std(returns) * (252 ** 0.5) if returns else 0
                    if volatility > 0.25:
                        risk_level = "高"
                    elif volatility > 0.15:
                        risk_level = "中高"
                    elif volatility > 0.08:
                        risk_level = "中"
                    else:
                        risk_level = "低"

                    # 近似夏普比率
                    rf = 0.02
                    avg_return = np.mean(returns) * 252
                    sharpe = (avg_return - rf) / volatility if volatility > 0 else 0
                else:
                    sharpe = 0.5
            else:
                sharpe = 0.5

            return FundEvalResult(
                code=code,
                name=name,
                score=round(score, 1),
                return_rank=rank,
                risk_level=risk_level,
                sharpe=round(sharpe, 2),
                max_drawdown=0,  # 需要完整历史才能精确算回撤
                fee_rate=1.5,    # 费率暂用默认值
            )

        except Exception as e:
            logger.warning(f"评价 {code} 失败，返回默认: {e}")
            return FundEvalResult(code=code, name="", score=50, return_rank=50, risk_level="中", sharpe=0.5, max_drawdown=0, fee_rate=1.5)

    @staticmethod
    async def search(keyword: str) -> list[dict]:
        """搜索基金"""
        if not keyword.strip():
            return []
        return await FundDataFetcher.search_funds(keyword)

    @staticmethod
    async def compare(codes: list[str]) -> list[FundEvalResult]:
        """对比多只基金评价"""
        results = []
        for code in codes:
            r = await FundEvalService.evaluate(code)
            results.append(r)
        return results

    @staticmethod
    async def get_top_ranked(limit: int = 20) -> list[dict]:
        """获取排名靠前的基金"""
        data = await FundDataFetcher.fetch_fund_rank()
        return data[:limit] if data else []
