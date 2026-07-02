"""交易策略 CRUD API

路由前缀：/api/v1/strategies
响应格式与其他模块保持一致：统一返回 ApiResponse(code=200, data=...)。
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.orm import Strategy
from ...models.schemas import ApiResponse, StrategyCreate, StrategyResponse, StrategyUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


# ── 工具函数 ─────────────────────────────────────────────────

def _now_iso() -> str:
    """返回 UTC 当前时间的 ISO-8601 字符串，精确到秒。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_response(s: Strategy) -> StrategyResponse:
    """将 ORM 对象转换为响应模型（反序列化 JSON 字段）。"""
    return StrategyResponse(
        id=s.id,
        name=s.name,
        description=s.description or "",
        target_code=s.target_code,
        target_name=s.target_name or "",
        target_type=s.target_type or "index",
        initial_capital=s.initial_capital,
        position_size=s.position_size,
        start_date=s.start_date,
        end_date=s.end_date or "",
        entry_rules=s.get_entry_rules(),
        exit_rules=s.get_exit_rules(),
        created_at=s.created_at or "",
        updated_at=s.updated_at or "",
    )


def _apply_data(orm_obj: Strategy, data: StrategyCreate | StrategyUpdate) -> None:
    """将 Pydantic 模型数据写入 ORM 对象（序列化 JSON 字段）。"""
    orm_obj.name            = data.name
    orm_obj.description     = data.description
    orm_obj.target_code     = data.target_code
    orm_obj.target_name     = data.target_name
    orm_obj.target_type     = data.target_type
    orm_obj.initial_capital = data.initial_capital
    orm_obj.position_size   = data.position_size
    orm_obj.start_date      = data.start_date
    orm_obj.end_date        = data.end_date
    orm_obj.set_entry_rules(data.entry_rules)
    orm_obj.set_exit_rules(data.exit_rules)


# ── 列出所有策略 ─────────────────────────────────────────────

@router.get("", summary="获取策略列表")
async def list_strategies(db: AsyncSession = Depends(get_db)):
    """返回所有已保存策略，按创建时间倒序排列（最新在前）。"""
    result = await db.execute(
        select(Strategy).order_by(Strategy.created_at.desc())
    )
    strategies = result.scalars().all()
    data = [_to_response(s).model_dump() for s in strategies]
    return ApiResponse(code=200, message="success", data=data)


# ── 创建策略 ──────────────────────────────────────────────────

@router.post("", summary="新建策略")
async def create_strategy(
    body: StrategyCreate,
    db: AsyncSession = Depends(get_db),
):
    """新建一条交易策略并持久化到数据库。"""
    now = _now_iso()
    s = Strategy(created_at=now, updated_at=now)
    _apply_data(s, body)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    logger.info("策略已创建: id=%s name=%r", s.id, s.name)
    return ApiResponse(code=200, message="创建成功", data=_to_response(s).model_dump())


# ── 获取单条策略 ──────────────────────────────────────────────

@router.get("/{strategy_id}", summary="获取策略详情")
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
):
    """按 ID 查询单条策略，不存在时返回 404。"""
    s = await db.get(Strategy, strategy_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略 ID={strategy_id} 不存在",
        )
    return ApiResponse(code=200, message="success", data=_to_response(s).model_dump())


# ── 更新策略 ──────────────────────────────────────────────────

@router.put("/{strategy_id}", summary="更新策略")
async def update_strategy(
    strategy_id: int,
    body: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """全量替换策略内容，同时更新 updated_at 时间戳。"""
    s = await db.get(Strategy, strategy_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略 ID={strategy_id} 不存在",
        )
    _apply_data(s, body)
    s.updated_at = _now_iso()
    await db.commit()
    await db.refresh(s)
    logger.info("策略已更新: id=%s name=%r", s.id, s.name)
    return ApiResponse(code=200, message="更新成功", data=_to_response(s).model_dump())


# ── 删除策略 ──────────────────────────────────────────────────

@router.delete("/{strategy_id}", summary="删除策略")
async def delete_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
):
    """按 ID 删除策略，不存在时返回 404。"""
    s = await db.get(Strategy, strategy_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略 ID={strategy_id} 不存在",
        )
    await db.delete(s)
    await db.commit()
    logger.info("策略已删除: id=%s", strategy_id)
    return ApiResponse(code=200, message="删除成功", data=None)
