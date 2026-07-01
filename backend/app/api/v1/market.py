"""市场扫描 API"""
from fastapi import APIRouter
from ...services.market_scan import MarketScanService
from ...models.schemas import ApiResponse

router = APIRouter(prefix="/api/v1/market", tags=["市场扫描"])


@router.get("/overview")
async def get_market_overview():
    """市场概览：指数估值、股债性价比"""
    data = await MarketScanService.get_market_overview()
    return ApiResponse(data=data.model_dump())


@router.get("/sectors")
async def get_hot_sectors():
    """热门行业板块"""
    data = await MarketScanService.get_hot_sectors()
    return ApiResponse(data=data)


@router.get("/undervalued")
async def get_undervalued():
    """低估指数推荐"""
    data = await MarketScanService.get_undervalued_indices()
    return ApiResponse(data=data)


@router.get("/north-flow")
async def get_north_flow():
    """北向资金流向"""
    data = await MarketScanService.get_north_flow()
    return ApiResponse(data=data)
