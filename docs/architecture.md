# 系统架构设计

## 一、架构概览

本系统采用前后端分离架构，后端基于 Python FastAPI 提供 RESTful API，
前端基于 Vue 3 + Vite + Element Plus 构建交互式数据看板。

```
┌──────────────────────────────────────────────────┐
│                   前端层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────┐ ┌─────────┐ │
│  │ Dashboard │ │ Portfolio│ │Funds │ │Market   │ │
│  │ 总览     │ │ 持仓分析  │ │基金池 │ │ 市场扫描 │ │
│  └──────────┘ └──────────┘ └──────┘ └─────────┘ │
│  Element Plus UI 组件 + ECharts 图表 + Axios 通信  │
└──────────────────────┬───────────────────────────┘
                       │ HTTP JSON (REST)
┌──────────────────────┴───────────────────────────┐
│                   后端层                           │
│  ┌──────────────────────────────────────────┐    │
│  │          FastAPI (uvicorn)               │    │
│  │  CORS / 路由 / 请求验证 / 自动文档         │    │
│  └──────┬─────────────────────┬─────────────┘    │
│         │                     │                   │
│  ┌──────┴──────┐    ┌────────┴────────┐          │
│  │  API v1     │    │   Services      │          │
│  │  /portfolio │    │   portfolio.py  │          │
│  │  /funds     │    │   fund_eval.py  │          │
│  │  /market    │    │   market_scan.py│          │
│  └──────┬──────┘    └────────┬────────┘          │
│         │                    │                    │
│  ┌──────┴────────────────────┴────────┐           │
│  │        Data Fetch 层               │           │
│  │  基金净值 / 市场指标 / 持仓数据采集   │           │
│  │  (akshare / tushare / 天天基金)     │           │
│  └──────────────┬────────────────────┘           │
│                 │                                │
│  ┌──────────────┴────────────────────┐           │
│  │          数据库 / 文件存储          │           │
│  │  SQLite (SQLAlchemy ORM)          │           │
│  │  CSV / Parquet (大量历史数据)       │           │
│  └───────────────────────────────────┘           │
└──────────────────────────────────────────────────┘
```

## 二、技术选型

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 后端框架 | FastAPI | 异步高性能，自动生成 OpenAPI 文档，Pydantic 校验 |
| 数据库 | SQLAlchemy + aiosqlite | 异步 ORM，轻量无需额外服务 |
| 数据计算 | Pandas + NumPy | 基金数据分析生态成熟 |
| 数据采集 | akshare / tushare | 开源免费，覆盖全市场的基金/股票数据 |
| 前端框架 | Vue 3 (Composition API) | 组件化开发，生态完善 |
| 前端 UI | Element Plus | 企业级 Vue 3 组件库，开箱即用 |
| 图表 | ECharts + vue-echarts | 金融图表丰富，性能好 |
| 构建 | Vite | 极速开发体验 |

## 三、目录结构

```
fund-stock-recommendation/
├── backend/
│   ├── requirements.txt       # Python 依赖
│   ├── run.py                 # 启动入口
│   └── app/
│       ├── main.py            # FastAPI 实例 & 注册
│       ├── config.py          # 配置管理
│       ├── database.py        # 数据库引擎 & 会话
│       ├── models/schemas.py  # Pydantic 模型
│       ├── api/v1/            # API 路由
│       │   ├── portfolio.py
│       │   ├── funds.py
│       │   └── market.py
│       ├── services/          # 业务逻辑
│       │   ├── portfolio.py
│       │   ├── fund_eval.py
│       │   └── market_scan.py
│       └── data_fetch/        # 数据采集
│           └── fund_data.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js            # 入口
│       ├── App.vue            # 根组件
│       ├── api/index.js       # Axios API 封装
│       ├── router/index.js    # 前端路由
│       ├── views/             # 页面视图
│       │   ├── Dashboard.vue
│       │   ├── Portfolio.vue
│       │   ├── Funds.vue
│       │   └── MarketScan.vue
│       ├── components/        # 公共组件
│       │   ├── AppLayout.vue
│       │   └── KpiCard.vue
│       └── styles/global.css  # 全局样式
├── data/                      # 本地数据存储
│   ├── raw/                   # 原始数据
│   ├── processed/             # 清洗后数据
│   └── portfolio/             # 用户持仓
├── notebooks/                 # Jupyter 实验
├── strategies/                # 策略配置
├── research/                  # 调研资料
└── docs/                      # 项目文档
    ├── architecture.md
    └── functional-design.md
```

## 四、数据流

```
[外部数据源]                   [用户]
   天天基金                       │
   akshare                       │ 手动录入持仓
   tushare                       ▼
      │                    ┌──────────────┐
      ▼                    │ portfolio/   │
  ┌─────────┐             │ holdings.csv │
  │ raw/    │────────────→│              │
  │ 基金净值 │  清洗/转换    └──────────────┘
  │ 市场指标 │                │
  └────┬────┘                ▼
       │               ┌──────────────┐
       │               │  Services    │
       └──────────────→│  分析计算     │
                       │  评价打分     │
                       │  机会识别     │
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │   API JSON   │
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │  Vue 前端    │
                       │  交互式看板   │
                       └──────────────┘
```

## 五、开发环境要求

| 工具 | 版本 |
|------|------|
| Python | >= 3.11 |
| Node.js | >= 18 |
| npm | >= 9 |

## 六、启动方式

### 后端
```bash
cd backend
pip install -r requirements.txt
python run.py
# → http://localhost:8000
# → API 文档: http://localhost:8000/docs
```

### 前端
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```
前端开发模式下自动代理 `/api` 请求到后端 `localhost:8000`。

## 七、后续演进

- 接入真实数据源（akshare）
- 实现用户认证
- 定时任务自动更新数据
- 持仓穿透分析（基金底层股票级）
- 策略回测引擎
- 微信/钉钉推送提醒
- PostgreSQL 替换 SQLite（数据量大时）
- Docker 容器化部署
