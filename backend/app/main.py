"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db, close_db
from .api.v1 import portfolio, funds, market


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时清理"""
    await init_db()
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


@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
