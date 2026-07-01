"""持仓分析服务 — CSV 持仓导入 + akshare 数据增强"""
import csv
import logging
import os
from typing import Optional

from ..config import settings
from ..data_fetch.fund_data import FundDataFetcher
from ..models.schemas import PortfolioSummary, HoldingBase

logger = logging.getLogger(__name__)


class PortfolioService:
    """持仓诊断与分析"""

    @staticmethod
    async def load_portfolio_csv() -> list[dict]:
        """
        从 data/portfolio/ 读取持仓 CSV
        列: fund_code, fund_name, shares, cost_basis, current_value, account
        current_value = 持仓总市值（非单位净值）
        """
        portfolio_dir = settings.portfolio_dir
        if not os.path.isdir(portfolio_dir):
            return []

        holdings = []
        for fname in os.listdir(portfolio_dir):
            if not fname.endswith(".csv"):
                continue
            fpath = os.path.join(portfolio_dir, fname)
            try:
                with open(fpath, encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        code = row.get("fund_code", "").strip()
                        if not code:
                            continue
                        holdings.append({
                            "fund_code": code,
                            "fund_name": row.get("fund_name", "").strip(),
                            "shares": float(row.get("shares", 0) or 0),
                            "cost_basis": float(row.get("cost_basis", 0) or 0),
                            "current_value": float(row.get("current_value", 0) or 0),
                            "account": row.get("account", "default").strip(),
                        })
                logger.info(f"已加载 {fname}: {len(holdings)} 条")
            except Exception as e:
                logger.warning(f"读取 {fname} 失败: {e}")
        return holdings

    @staticmethod
    async def analyze(holdings: Optional[list[dict]] = None) -> PortfolioSummary:
        """分析持仓：总市值、总成本、收益"""
        if holdings is None:
            holdings = await PortfolioService.load_portfolio_csv()
        if not holdings:
            holdings = await PortfolioService.get_mock_holdings()

        items = [HoldingBase(**h) for h in holdings]
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
    async def get_mock_holdings() -> list[dict]:
        """兜底 mock 数据（5 只基金）"""
        return [
            {"fund_code": "110011", "fund_name": "易方达中小盘混合", "shares": 5000, "cost_basis": 8.5, "current_value": 9.2, "account": "支付宝"},
            {"fund_code": "005827", "fund_name": "中欧时代先锋股票", "shares": 3000, "cost_basis": 2.1, "current_value": 2.45, "account": "支付宝"},
            {"fund_code": "000311", "fund_name": "景顺长城沪深300增强", "shares": 8000, "cost_basis": 1.8, "current_value": 1.95, "account": "支付宝"},
            {"fund_code": "002190", "fund_name": "农银新能源主题", "shares": 4000, "cost_basis": 3.2, "current_value": 2.88, "account": "支付宝"},
            {"fund_code": "008283", "fund_name": "易方达消费行业股票", "shares": 6000, "cost_basis": 4.5, "current_value": 4.12, "account": "支付宝"},
        ]

    @staticmethod
    async def get_asset_allocation(holdings: Optional[list[dict]] = None) -> dict:
        """资产配置（按基金代码粗略分类）"""
        if holdings is None:
            holdings = await PortfolioService.load_portfolio_csv()
        total = sum(float(h.get("current_value", 0)) for h in holdings) or 1
        equity = bond = commodity = monetary = 0.0
        for h in holdings:
            code = h.get("fund_code", "")
            val = float(h.get("current_value", 0))
            if code in ("002611",):
                commodity += val
            elif code in ("012348", "016186", "013275"):
                bond += val
            else:
                equity += val
        return {
            "equity": round(equity / total * 100, 1),
            "bond": round(bond / total * 100, 1),
            "commodity": round(commodity / total * 100, 1),
            "monetary": round(monetary / total * 100, 1),
        }

    @staticmethod
    async def get_sector_exposure(holdings: Optional[list[dict]] = None) -> list[dict]:
        """
        行业暴露分析：穿透到底层重仓股 → 映射行业 → 按组合权重汇总
        """
        if holdings is None:
            holdings = await PortfolioService.load_portfolio_csv()
        if not holdings:
            return [{"sector": "暂无数据", "ratio": 100}]

        total_value = sum(float(h.get("current_value", 0) or 0) for h in holdings) or 1
        sector_contrib = {}  # sector -> weighted total

        for h in holdings:
            code = h.get("fund_code", "")
            fund_val = float(h.get("current_value", 0) or 0)
            fund_weight = fund_val / total_value

            positions = await FundDataFetcher.fetch_fund_position(code)
            if not positions:
                continue
            for pos in positions:
                stock_code = str(pos.get("stock_code", "")).strip()
                ratio = float(pos.get("ratio", 0) or 0) / 100
                sector = FundDataFetcher.lookup_sector(stock_code, str(pos.get("stock", "")))
                sector_contrib[sector] = sector_contrib.get(sector, 0) + fund_weight * ratio

        # 归一化到百分比
        total_penetrated = sum(sector_contrib.values()) or 1
        result = [{"sector": k, "ratio": round(v / total_penetrated * 100, 1)}
                  for k, v in sector_contrib.items()]
        result.sort(key=lambda x: x["ratio"], reverse=True)
        return result if result else [{"sector": "暂无行业数据", "ratio": 100}]

    @staticmethod
    async def detect_overlap(holdings: Optional[list[dict]] = None) -> list[dict]:
        """
        持仓重叠检测：找出被多只基金共同持有的股票
        """
        if holdings is None:
            holdings = await PortfolioService.load_portfolio_csv()
        if not holdings:
            return []

        stock_funds = {}  # stock_code -> { stock, funds, total_ratio }
        for h in holdings:
            code = h.get("fund_code", "")
            positions = await FundDataFetcher.fetch_fund_position(code)
            if not positions:
                continue
            for pos in positions:
                sc = str(pos.get("stock_code", "")).strip()
                if not sc:
                    continue
                if sc not in stock_funds:
                    stock_funds[sc] = {
                        "stock": pos.get("stock", ""),
                        "funds": [],
                        "total_ratio": 0.0,
                    }
                stock_funds[sc]["funds"].append(code)
                stock_funds[sc]["total_ratio"] = round(stock_funds[sc]["total_ratio"] + float(pos.get("ratio", 0) or 0), 2)

        overlaps = [v for v in stock_funds.values() if len(v["funds"]) > 1]
        overlaps.sort(key=lambda x: len(x["funds"]), reverse=True)
        return overlaps

    @staticmethod
    async def get_risk_metrics(holdings: Optional[list[dict]] = None) -> dict:
        """TODO: 基于净值历史计算风险指标"""
        return {"volatility": 0, "max_drawdown": 0, "sharpe_ratio": 0, "avg_correlation": 0, "var_95": 0}
    @staticmethod
    async def save_holdings(holdings: list[dict]) -> list[dict]:
        """
        保存持仓到 CSV，自动用 akshare 最新净值计算当前市值
        current_value = shares * nav_per_unit
        """
        portfolio_dir = settings.portfolio_dir
        os.makedirs(portfolio_dir, exist_ok=True)

        enriched = []
        for h in holdings:
            code = h.get("fund_code", "").strip()
            if not code:
                continue
            shares = float(h.get("shares", 0) or 0)
            cost_basis = float(h.get("cost_basis", 0) or 0)
            # 拉取最新净值计算总市值
            nav = await FundDataFetcher.fetch_latest_nav(code)
            current_value = round(shares * nav, 2) if nav and shares else float(h.get("current_value", 0) or 0)
            enriched.append({
                "fund_code": code,
                "fund_name": h.get("fund_name", "").strip(),
                "shares": shares,
                "cost_basis": cost_basis,
                "current_value": current_value,
                "account": h.get("account", "default").strip(),
            })

        # 写回 CSV
        fpath = os.path.join(portfolio_dir, "alipay_portfolio.csv")
        with open(fpath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["fund_code", "fund_name", "shares", "cost_basis", "current_value", "account"])
            writer.writeheader()
            writer.writerows(enriched)

        logger.info(f"已保存 {len(enriched)} 条持仓到 {fpath}")
        return enriched
