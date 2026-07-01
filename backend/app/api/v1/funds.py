"""基金数据 API"""
from fastapi import APIRouter, Query
from ...services.fund_eval import FundEvalService
from ...models.schemas import ApiResponse

router = APIRouter(prefix="/api/v1/funds", tags=["基金数据"])


@router.get("/search")
async def search_funds(keyword: str = Query("", description="搜索关键词")):
    """搜索基金"""
    results = await FundEvalService.search(keyword)
    return ApiResponse(data=results)


@router.get("/evaluate/{code}")
async def evaluate_fund(code: str):
    """基金综合评价"""
    result = await FundEvalService.evaluate(code)
    return ApiResponse(data=result.model_dump())


@router.get("/compare")
async def compare_funds(codes: str = Query("", description="基金代码，逗号分隔")):
    """对比多只基金"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    results = await FundEvalService.compare(code_list)
    return ApiResponse(data=[r.model_dump() for r in results])


@router.get("/nav/{code}")
async def get_fund_nav(code: str):
    """基金历史净值"""
    from ...data_fetch.fund_data import FundDataFetcher
    data = await FundDataFetcher.fetch_fund_nav(code)
    return ApiResponse(data=data)


@router.get("/position/{code}")
async def get_fund_position(code: str):
    """基金持仓（前十大重仓股）"""
    from ...data_fetch.fund_data import FundDataFetcher
    data = await FundDataFetcher.fetch_fund_position(code)
    return ApiResponse(data=data)
