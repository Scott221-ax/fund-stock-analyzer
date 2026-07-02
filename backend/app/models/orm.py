"""SQLAlchemy ORM 模型定义

每个 ORM 类继承 database.Base，init_db() 启动时会自动建表。
entry_rules / exit_rules 以 JSON 字符串存储，读写时通过
json.loads / json.dumps 转换。
"""
import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text
from ..database import Base


def _now_iso() -> str:
    """返回 UTC 当前时间的 ISO-8601 字符串，精确到秒。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Strategy(Base):
    """用户自定义交易策略持久化表。

    JSON 字段（entry_rules / exit_rules）存为 TEXT，
    应用层通过 json.loads / json.dumps 处理。
    """
    __tablename__ = "strategies"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String(200), nullable=False)
    description     = Column(Text,    default="", nullable=False)
    target_code     = Column(String(20),  nullable=False)
    target_name     = Column(String(100), default="", nullable=False)
    # "index"（指数）或 "fund"（基金）
    target_type     = Column(String(20),  default="index", nullable=False)
    initial_capital = Column(Float, default=100000.0, nullable=False)
    position_size   = Column(Float, default=10000.0,  nullable=False)
    start_date      = Column(String(20), nullable=False)
    end_date        = Column(String(20), default="",  nullable=False)
    # 入场规则列表，JSON 字符串，如 '[{"type":"ma_cross",...}]'
    entry_rules     = Column(Text, default="[]", nullable=False)
    # 出场规则列表，JSON 字符串，如 '[{"type":"take_profit","value":10}]'
    exit_rules      = Column(Text, default="[]", nullable=False)
    created_at      = Column(String(30), default=_now_iso, nullable=False)
    updated_at      = Column(String(30), default=_now_iso, onupdate=_now_iso, nullable=False)

    # ── 便利方法：JSON 字段的读写 ────────────────────────────

    def get_entry_rules(self) -> list[dict]:
        """将 entry_rules 字段从 JSON 字符串反序列化为 list。"""
        try:
            return json.loads(self.entry_rules or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def set_entry_rules(self, rules: list[dict]) -> None:
        self.entry_rules = json.dumps(rules, ensure_ascii=False)

    def get_exit_rules(self) -> list[dict]:
        """将 exit_rules 字段从 JSON 字符串反序列化为 list。"""
        try:
            return json.loads(self.exit_rules or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def set_exit_rules(self, rules: list[dict]) -> None:
        self.exit_rules = json.dumps(rules, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Strategy id={self.id} name={self.name!r}>"
