"""持仓分析服务"""
from typing import Optional
from ..models.schemas import PortfolioSummary, HoldingBase


class PortfolioService:
    """持仓诊断与分析"""

    @staticmethod
    async def analyze(holdings: list[dict]) -> PortfolioSummary:
        """
        分析持仓：计算总市值、收益、各类指标
        当前返回 mock 数据，后续接入真实计算
        """
        items = [HoldingBase(**h) for h in holdings] if holdings else []

        total_value = sum(h.current_value for h in items)
        total_cost = sum(h.cost_basis for h in items)
        total_return = total_value - total_cost
        total_return_pct = (total_return / total_cost * 100) if total_cost else 0

        return PortfolioSummary(
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2),
            total_return=round(total_return, 2),
            total_return_pct=round(total_return_pct, 2),
            fund_count=len(items),
            holdings=items,
        )

    @staticmethod
    async def get_asset_allocation(holdings: list[dict]) -> dict:
        """
        资产配置分析（股/债/商品/货币）
        """
        # TODO: 穿透基金持仓，统计大类资产比例
        return {
            "equity": 65.0,
            "bond": 20.0,
            "commodity": 5.0,
            "monetary": 10.0,
        }

    @staticmethod
    async def get_sector_exposure(holdings: list[dict]) -> list[dict]:
        """
        行业暴露分析
        """
        # TODO: 穿透到基金底层股票，统计行业分布
        return [
            {"sector": "食品饮料", "ratio": 18.5},
            {"sector": "医药生物", "ratio": 15.2},
            {"sector": "电子", "ratio": 12.8},
            {"sector": "电力设备", "ratio": 11.3},
            {"sector": "银行", "ratio": 8.7},
        ]

    @staticmethod
    async def detect_overlap(holdings: list[dict]) -> list[dict]:
        """
        检测持仓重叠：不同基金共同持有的股票
        """
        # TODO: 基于基金季报前十持仓做重叠分析
        return [
            {"stock": "贵州茅台", "funds": 3, "total_ratio": 12.5},
            {"stock": "宁德时代", "funds": 2, "total_ratio": 8.3},
        ]

    @staticmethod
    async def get_risk_metrics(holdings: list[dict]) -> dict:
        """
        风险指标：波动率、最大回撤、夏普比率、相关性
        """
        # TODO: 基于历史净值数据计算
        return {
            "volatility": 18.5,
            "max_drawdown": -22.3,
            "sharpe_ratio": 0.85,
            "avg_correlation": 0.62,
            "var_95": -3.2,
        }

    @staticmethod
    async def get_mock_portfolio() -> PortfolioSummary:
        """返回一份示例持仓数据，供前端开发用"""
        mock_holdings = [
            HoldingBase(fund_code="110011", fund_name="易方达中小盘混合", shares=5000, cost_basis=8.5, current_value=9.2, account="支付宝"),
            HoldingBase(fund_code="005827", fund_name="中欧时代先锋股票", shares=3000, cost_basis=2.1, current_value=2.45, account="支付宝"),
            HoldingBase(fund_code="000311", fund_name="景顺长城沪深300增强", shares=8000, cost_basis=1.8, current_value=1.95, account="支付宝"),
            HoldingBase(fund_code="002190", fund_name="农银新能源主题", shares=4000, cost_basis=3.2, current_value=2.88, account="支付宝"),
            HoldingBase(fund_code="008283", fund_name="易方达消费行业股票", shares=6000, cost_basis=4.5, current_value=4.12, account="支付宝"),
        ]
        return await PortfolioService.analyze([h.model_dump() for h in mock_holdings])
