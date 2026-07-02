"""交易回测引擎 — 支持自定义交易规则的历史走势分析"""
import asyncio
import logging
import math
from datetime import date, datetime

import akshare as ak
import numpy as np
import pandas as pd

from ..data_fetch.fund_data import FundDataFetcher
from ..models.schemas import BacktestRequest, BacktestResult, TradeRecord

logger = logging.getLogger(__name__)


class BacktestEngine:

    @staticmethod
    async def run(req: BacktestRequest) -> BacktestResult:
        data = await BacktestEngine._fetch_data(req)
        if not data or len(data) < 30:
            return BacktestResult(strategy_name=req.name, target_name=req.target_name)
        indicators = BacktestEngine._calc_indicators(data)
        sim = BacktestEngine._simulate(indicators, req)
        return BacktestEngine._compute_metrics(sim, req)

    @staticmethod
    async def _fetch_data(req: BacktestRequest) -> list[dict]:
        code = req.target_code
        s = date.fromisoformat(req.start_date) if req.start_date else date(2020, 1, 1)
        e = date.fromisoformat(req.end_date) if req.end_date else date.today()
        try:
            if req.target_type == "index":
                df = await asyncio.to_thread(ak.stock_zh_index_hist_csindex,
                    symbol=code, start_date=s.strftime("%Y%m%d"), end_date=e.strftime("%Y%m%d"))
                if df is None or df.empty:
                    return []
                df = df.rename(columns={"日期": "date", "收盘": "price"})
                df["date"] = df["date"].astype(str)
                return df[["date", "price"]].to_dict(orient="records")
            return await FundDataFetcher.fetch_fund_nav(code, s, e)
        except Exception as ex:
            logger.warning(f"获取数据失败: {ex}")
            return []

    @staticmethod
    def _calc_indicators(data: list[dict]) -> list[dict]:
        df = pd.DataFrame(data)
        df["price"] = df[["price" if "price" in df.columns else "nav"]].astype(float)
        for p in [5, 10, 20, 30, 60]:
            df[f"ma{p}"] = df["price"].rolling(p).mean()
        for s, l in [(5, 20), (10, 30)]:
            ps, pl = df[f"ma{s}"].shift(1), df[f"ma{l}"].shift(1)
            above = df[f"ma{s}"] > df[f"ma{l}"]
            df[f"golden_cross_{s}_{l}"] = above & ~(ps > pl)
            df[f"death_cross_{s}_{l}"] = ~above & (ps > pl)
        delta = df["price"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = (100 - 100 / (1 + rs)).fillna(50)
        df["pct_5d"] = df["price"].pct_change(5) * 100
        df["pct_20d"] = df["price"].pct_change(20) * 100
        df["high_20d"] = df["price"].rolling(20).max()
        df["from_high_20d"] = (df["price"] - df["high_20d"]) / df["high_20d"] * 100
        return df.fillna(0).replace([np.inf, -np.inf], 0).to_dict(orient="records")

    @staticmethod
    def _check_entry(row: dict, rules: list[dict]) -> bool:
        for r in rules:
            t, p, d = r.get("type", ""), r.get("params", {}), r.get("direction", "golden")
            if t == "ma_cross":
                s, l = p.get("short", 5), p.get("long", 20)
                if d == "golden" and row.get(f"golden_cross_{s}_{l}"):
                    return True
                if d == "death" and row.get(f"death_cross_{s}_{l}"):
                    return True
            elif t == "price_below_ma":
                pr, mv = float(row.get("price", 0)), float(row.get(f"ma{p.get('ma',20)}", 0))
                if mv > 0 and pr < mv:
                    return True
            elif t == "rsi_below":
                if 0 < float(row.get("rsi", 50)) < p.get("threshold", 30):
                    return True
        return False

    @staticmethod
    def _check_exit(row, ep, cp, ed, cd, rules) -> str:
        for r in rules:
            t, v, p = r.get("type"), r.get("value", 0), r.get("params", {})
            if t == "take_profit" and cp >= ep * (1 + v / 100):
                return f"take_profit+{v}%"
            if t == "stop_loss" and cp <= ep * (1 + v / 100):
                return f"stop_loss{v}%"
            if t == "holding_days" and ed and cd:
                try:
                    h = (datetime.strptime(cd, "%Y-%m-%d") - datetime.strptime(ed, "%Y-%m-%d")).days
                    if h >= v:
                        return f"holding_{v}d"
                except ValueError:
                    pass
        return ""

    @staticmethod
    def _simulate(data: list[dict], req: BacktestRequest) -> dict:
        cash, pos, ep, ed = req.initial_capital, 0.0, 0.0, ""
        trades, curve = [], []
        for row in data:
            pr = float(row.get("price", 0))
            if pr <= 0:
                continue
            ds = row.get("date", "")
            curve.append({"date": ds, "value": round(cash + pos * pr, 2)})
            if pos > 1e-8:
                reason = BacktestEngine._check_exit(row, ep, pr, ed, ds, req.exit_rules)
                if reason:
                    ret = (pr - ep) / ep * 100
                    trades.append(TradeRecord(entry_date=ed, entry_price=round(ep, 4),
                        exit_date=ds, exit_price=round(pr, 4), shares=round(pos, 4),
                        return_pct=round(ret, 2), profit=round(pos * pr - pos * ep, 2),
                        exit_reason=reason))
                    cash, pos, ep, ed = pos * pr, 0.0, 0.0, ""
            elif BacktestEngine._check_entry(row, req.entry_rules):
                amt = min(req.position_size, cash)
                if amt > 0:
                    pos, ep, ed, cash = amt / pr, pr, ds, cash - amt
        if pos > 1e-8 and data:
            lp = float(data[-1].get("price", 0))
            if lp > 0:
                ret = (lp - ep) / ep * 100
                trades.append(TradeRecord(entry_date=ed, entry_price=round(ep, 4),
                    exit_date=data[-1]["date"], exit_price=round(lp, 4), shares=round(pos, 4),
                    return_pct=round(ret, 2), profit=round(pos * lp - pos * ep, 2),
                    exit_reason="final_close"))
                cash += pos * lp
        return {"final_equity": round(cash, 2), "trades": trades, "equity_curve": curve}

    @staticmethod
    def _compute_metrics(sim: dict, req: BacktestRequest) -> BacktestResult:
        trades, curve = sim["trades"], sim["equity_curve"]
        n = len(trades)
        if n == 0:
            return BacktestResult(strategy_name=req.name, target_name=req.target_name,
                initial_capital=req.initial_capital, final_equity=sim["final_equity"], equity_curve=curve)
        wins, losses = [t for t in trades if t.profit > 0], [t for t in trades if t.profit <= 0]
        wr = len(wins) / n * 100
        aw = sum(t.return_pct for t in wins) / len(wins) if wins else 0
        al = sum(t.return_pct for t in losses) / len(losses) if losses else 0
        pf = abs(sum(t.profit for t in wins) / max(sum(t.profit for t in losses), 1e-10))
        tr = (sim["final_equity"] - req.initial_capital) / req.initial_capital * 100
        annual = 0.0
        if len(curve) > 1:
            try:
                days = (datetime.strptime(curve[-1]["date"], "%Y-%m-%d") - datetime.strptime(curve[0]["date"], "%Y-%m-%d")).days
                annual = ((1 + tr / 100) ** (365 / max(days, 1)) - 1) * 100 if days > 0 else 0
            except ValueError:
                pass
        eqs = [c["value"] for c in curve]
        peak, mdd = eqs[0] if eqs else 0, 0.0
        for v in eqs:
            if v > peak:
                peak = v
            dd = (peak - v) / peak * 100 if peak > 0 else 0
            if dd > mdd:
                mdd = dd
        dr = [(eqs[i] / eqs[i-1] - 1) for i in range(1, len(eqs)) if eqs[i-1] > 0]
        sharpe = 0.0
        if len(dr) > 5:
            a, s = np.mean(dr) * 252, np.std(dr) * math.sqrt(252)
            sharpe = round((a - 0.02) / s, 2) if s > 1e-10 else 0.0
        return BacktestResult(strategy_name=req.name, target_name=req.target_name,
            initial_capital=req.initial_capital, final_equity=sim["final_equity"],
            total_return_pct=round(tr, 2), annualized_return=round(annual, 2),
            max_drawdown=round(mdd, 2), sharpe_ratio=sharpe,
            total_trades=n, winning_trades=len(wins), losing_trades=len(losses),
            win_rate=round(wr, 1), avg_win_pct=round(aw, 2), avg_loss_pct=round(al, 2),
            profit_factor=round(pf, 2), trades=trades, equity_curve=curve)
