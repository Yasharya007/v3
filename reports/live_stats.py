"""
live_stats.py  (robust rebuild)

Key change vs the original:
  - Current equity is derived DIRECTLY from portfolio.csv + capital.csv,
    so it never breaks when equity_history.csv has missing columns.
  - equity_history.csv is used ONLY for path-dependent stats
    (max drawdown, true CAGR), and only if it actually contains
    valid Total_Equity values. Otherwise those are reported as
    "needs history" instead of crashing or printing garbage.
  - Total return is measured against INITIAL_CAPITAL from config
    (the real cost basis of the account), not the first equity row.

Run from the project root:  python -m reports.live_stats
"""

import os
import pandas as pd

try:
    from config import INITIAL_CAPITAL
except Exception:
    INITIAL_CAPITAL = 100000.0


DATA = "data"


def _load(name):
    return pd.read_csv(os.path.join(DATA, name))


def print_live_stats():
    portfolio = _load("portfolio.csv")
    trades = _load("trades.csv")
    cash = float(_load("capital.csv")["Cash"].iloc[0])

    # ---- current equity straight from the intact files ----
    mkt_value = float(portfolio["Current_Value"].sum()) if len(portfolio) else 0.0
    invested = float(portfolio["Invested_Value"].sum()) if len(portfolio) else 0.0
    current_equity = cash + mkt_value
    unrealized = float(portfolio["PnL"].sum()) if len(portfolio) else 0.0

    total_return = (current_equity / INITIAL_CAPITAL - 1) * 100

    # ---- path-dependent stats from equity_history (only if valid) ----
    cagr = None
    max_drawdown = None
    days_live = None
    try:
        eq = _load("equity_history.csv")
        eq = eq[eq["Total_Equity"].notna()].copy()
        if len(eq) >= 2:
            eq["Date"] = pd.to_datetime(eq["Date"])
            eq = eq.sort_values("Date")
            days_live = (eq["Date"].iloc[-1] - eq["Date"].iloc[0]).days
            curve = eq["Total_Equity"].astype(float)
            dd = (curve / curve.cummax() - 1) * 100
            max_drawdown = float(dd.min())
            years = days_live / 365.25
            # Only annualize once there's enough runway to be meaningful.
            if years >= 0.5:
                cagr = ((current_equity / INITIAL_CAPITAL) ** (1 / years) - 1) * 100
    except FileNotFoundError:
        pass

    # ---- trade stats ----
    n_trades = len(trades)
    win_rate = None
    avg_win = avg_loss = None
    if n_trades > 0 and "PnL" in trades:
        winners = trades[trades["PnL"] > 0]
        win_rate = len(winners) / n_trades * 100
        if len(winners):
            avg_win = float(winners["PnL"].mean())
        losers = trades[trades["PnL"] <= 0]
        if len(losers):
            avg_loss = float(losers["PnL"].mean())

    # ---- output ----
    p = print
    p("\n===== LIVE PORTFOLIO =====\n")
    p(f"Current Equity   : Rs {current_equity:,.2f}")
    p(f"  Cash           : Rs {cash:,.2f}  ({cash/current_equity*100:.1f}%)")
    p(f"  Invested (mkt) : Rs {mkt_value:,.2f}  ({mkt_value/current_equity*100:.1f}%)")
    p(f"Initial Capital  : Rs {INITIAL_CAPITAL:,.2f}")
    p(f"Open Positions   : {len(portfolio)}")
    p()
    p(f"Total Return     : {total_return:+.2f}%")
    p(f"Unrealized P&L   : Rs {unrealized:+,.2f}")

    if max_drawdown is not None:
        p(f"Max Drawdown     : {max_drawdown:.2f}%   (over {days_live} days)")
    else:
        p("Max Drawdown     : needs valid equity_history "
          "(run rebuild_equity_history.py)")

    if cagr is not None:
        p(f"CAGR             : {cagr:+.2f}%")
    elif days_live is not None:
        p(f"CAGR             : not meaningful yet "
          f"({days_live} days live; wait for >~6 months)")
    else:
        p("CAGR             : needs valid equity_history")

    p(f"\nClosed Trades    : {n_trades}")
    if win_rate is not None:
        p(f"Win Rate         : {win_rate:.2f}%")
        if avg_win is not None:
            p(f"Avg Win          : Rs {avg_win:+,.2f}")
        if avg_loss is not None:
            p(f"Avg Loss         : Rs {avg_loss:+,.2f}")
    else:
        p("Win Rate         : N/A (no closed trades yet)")

    if len(portfolio):
        p("\nPositions (best -> worst):")
        for _, r in portfolio.sort_values("Return_%", ascending=False).iterrows():
            p(f"  {r['Ticker']:<14} {r['Return_%']:+6.2f}%   "
              f"Rs {r['PnL']:+9,.2f}   (in since {r['Entry_Date']})")


if __name__ == "__main__":
    print_live_stats()