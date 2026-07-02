"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db, close_db
from .api.v1 import portfolio, funds, market
from .api.v1 import backtest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时清理"""
    await init_db()
    # 后台预热缓存（不阻塞启动）
    async def _warmup():
        try:
            from .services.market_scan import MarketScanService
            import logging as _log
            _log.getLogger(__name__).info("预热缓存：市场概览...")
            await MarketScanService.get_market_overview()
            # 预热基金列表
            from .data_fetch.fund_data import FundDataFetcher
            await FundDataFetcher.search_funds("")
            _log.getLogger(__name__).info("缓存预热完成")
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).warning(f"缓存预热失败: {e}")
    import asyncio as _aio
    _aio.create_task(_warmup())
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基金持仓智能分析与市场机会扫描系统",
    lifespan=lifespan,
)

# CORS — 开发环境允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(portfolio.router)
app.include_router(funds.router)
app.include_router(market.router)
app.include_router(backtest.router)


@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
