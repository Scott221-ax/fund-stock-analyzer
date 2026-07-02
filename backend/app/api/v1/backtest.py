"""交易回测 API"""
from fastapi import APIRouter
from ...services.backtest import BacktestEngine
from ...models.schemas import BacktestRequest, ApiResponse

router = APIRouter(prefix="/api/v1/backtest", tags=["交易回测"])


@router.post("/run")
async def run_backtest(req: BacktestRequest):
    """运行回测"""
    result = await BacktestEngine.run(req)
    return ApiResponse(data=result.model_dump())


@router.get("/presets")
async def get_presets():
    """获取预设策略"""
    presets = [
        {
            "name": "均线金叉买入",
            "target_code": "000300",
            "target_name": "沪深300",
            "target_type": "index",
            "initial_capital": 100000,
            "position_size": 10000,
            "entry_rules": [{"type": "ma_cross", "params": {"short": 5, "long": 20}, "direction": "golden"}],
            "exit_rules": [{"type": "take_profit", "value": 10}, {"type": "stop_loss", "value": -5}],
            "start_date": "2020-01-01",
            "end_date": "",
        },
        {
            "name": "RSI超卖反弹",
            "target_code": "000300",
            "target_name": "沪深300",
            "target_type": "index",
            "initial_capital": 100000,
            "position_size": 10000,
            "entry_rules": [{"type": "rsi_below", "params": {"threshold": 30}}],
            "exit_rules": [{"type": "take_profit", "value": 8}, {"type": "holding_days", "value": 30}],
            "start_date": "2020-01-01",
            "end_date": "",
        },
        {
            "name": "价格跌破均线买入",
            "target_code": "000300",
            "target_name": "沪深300",
            "target_type": "index",
            "initial_capital": 100000,
            "position_size": 10000,
            "entry_rules": [{"type": "price_below_ma", "params": {"ma": 20}}],
            "exit_rules": [{"type": "take_profit", "value": 10}, {"type": "stop_loss", "value": -5}],
            "start_date": "2020-01-01",
            "end_date": "",
        },
        {
            "name": "QQQ 均线策略",
            "target_code": "QQQ",
            "target_name": "纳斯达克100",
            "target_type": "us_stock",
            "initial_capital": 100000,
            "position_size": 10000,
            "entry_rules": [{"type": "ma_cross", "params": {"short": 5, "long": 20}, "direction": "golden"}],
            "exit_rules": [{"type": "take_profit", "value": 8}, {"type": "stop_loss", "value": -5}],
            "start_date": "2020-01-01",
            "end_date": "",
        },
    ]
    return ApiResponse(data=presets)
