# FundStock Analyzer — 基金持仓智能分析系统

本地运行的基金持仓分析与市场机会扫描工具。

## 快速启动

### 后端
```bash
cd backend
pip install -r requirements.txt
python run.py
```
访问 http://localhost:8000/docs 查看 API 文档。

### 前端
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:5173 使用交互式看板。

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy + SQLite + Pandas
- **前端**: Vue 3 + Vite + Element Plus + ECharts

## 文档

- [架构设计](docs/architecture.md)
- [功能设计](docs/functional-design.md)

## 项目结构

```
backend/     — Python FastAPI 后端
frontend/    — Vue 3 前端
data/        — 本地数据存储
docs/        — 项目文档
notebooks/   — Jupyter 实验
strategies/  — 策略配置
research/    — 调研资料
```
