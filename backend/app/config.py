"""应用配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FundStock Analyzer"
    app_version: str = "0.1.0"
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/fund_stock.db"

    # 数据目录
    data_dir: str = "data"
    portfolio_dir: str = "data/portfolio"
    raw_data_dir: str = "data/raw"
    processed_dir: str = "data/processed"

    # 外部 API 配置（后续接入真实数据源时使用）
    tushare_token: str = ""
    akshare_enabled: bool = True

    # CORS（开发环境允许前端跨域）
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
