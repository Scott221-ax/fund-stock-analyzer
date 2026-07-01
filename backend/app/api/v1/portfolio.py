"""持仓分析 API"""
from fastapi import APIRouter
from ...services.portfolio import PortfolioService
from ...models.schemas import ApiResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["持仓分析"])


@router.get("/summary")
async def get_portfolio_summary():
    """获取持仓总览（自动加载 CSV，回退 mock）"""
    summary = await PortfolioService.analyze()
    return ApiResponse(data=summary.model_dump())


@router.get("/holdings")
async def get_holdings():
    """获取原始持仓列表（CSV 数据）"""
    data = await PortfolioService.load_portfolio_csv()
    return ApiResponse(data=data)


@router.put("/holdings")
async def save_holdings(holdings: list[dict]):
    """保存持仓（覆盖 CSV，自动计算最新市值）"""
    data = await PortfolioService.save_holdings(holdings)
    return ApiResponse(data=data)


@router.get("/allocation")
async def get_asset_allocation():
    """资产配置比例"""
    data = await PortfolioService.get_asset_allocation([])
    return ApiResponse(data=data)


@router.get("/sectors")
async def get_sector_exposure():
    """行业暴露分析"""
    data = await PortfolioService.get_sector_exposure([])
    return ApiResponse(data=data)


@router.get("/overlap")
async def get_overlap():
    """持仓重叠检测"""
    data = await PortfolioService.detect_overlap([])
    return ApiResponse(data=data)


@router.get("/risk")
async def get_risk_metrics():
    """风险指标"""
    data = await PortfolioService.get_risk_metrics([])
    return ApiResponse(data=data)
