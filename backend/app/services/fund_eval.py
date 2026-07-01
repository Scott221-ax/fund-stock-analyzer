"""基金评价服务"""
from ..models.schemas import FundEvalResult


class FundEvalService:
    """单只基金的评分与诊断"""

    @staticmethod
    async def evaluate(code: str) -> FundEvalResult:
        """
        综合评价一只基金：收益、风险、费率、经理等维度
        当前返回 mock 数据，后续接入真实计算
        """
        # TODO: 接入净值数据 → 计算夏普/回撤/排名
        mock_db = {
            "110011": FundEvalResult(code="110011", name="易方达中小盘混合", score=82, return_rank=25, risk_level="中", sharpe=0.92, max_drawdown=-18.5, fee_rate=1.75),
            "005827": FundEvalResult(code="005827", name="中欧时代先锋股票", score=78, return_rank=30, risk_level="中高", sharpe=0.78, max_drawdown=-22.1, fee_rate=1.50),
            "000311": FundEvalResult(code="000311", name="景顺长城沪深300增强", score=75, return_rank=40, risk_level="中", sharpe=0.65, max_drawdown=-20.8, fee_rate=1.20),
        }
        result = mock_db.get(code)
        if result:
            return result
        return FundEvalResult(code=code, name="未知基金", score=50, return_rank=50, risk_level="中", sharpe=0.5, max_drawdown=-15.0, fee_rate=1.5)

    @staticmethod
    async def search(keyword: str) -> list[dict]:
        """搜索基金"""
        # TODO: 对接基金数据库查询
        all_funds = [
            {"code": "110011", "name": "易方达中小盘混合", "type": "混合型"},
            {"code": "005827", "name": "中欧时代先锋股票", "type": "股票型"},
            {"code": "000311", "name": "景顺长城沪深300增强", "type": "指数型"},
            {"code": "002190", "name": "农银新能源主题", "type": "股票型"},
            {"code": "008283", "name": "易方达消费行业股票", "type": "股票型"},
        ]
        if keyword:
            return [f for f in all_funds if keyword.lower() in f["name"].lower() or keyword in f["code"]]
        return all_funds

    @staticmethod
    async def compare(codes: list[str]) -> list[FundEvalResult]:
        """对比多只基金"""
        results = []
        for code in codes:
            r = await FundEvalService.evaluate(code)
            results.append(r)
        return results
