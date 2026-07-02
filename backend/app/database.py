"""数据库引擎与会话管理"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


# 确保数据目录存在
os.makedirs(os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", "")), exist_ok=True)

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """创建所有表（需先导入 ORM 模型，确保 metadata 已注册）"""
    # 导入 ORM 模型，触发 Strategy 等类注册到 Base.metadata
    from .models import orm  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库引擎"""
    await engine.dispose()
