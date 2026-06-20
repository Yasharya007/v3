"""
rebuild_equity_history.py

Reconstructs a proper DAILY equity curve and overwrites the broken
equity_history.csv (whose Portfolio_Value / Total_Equity columns are blank).

It does NOT trust the old equity_history.csv at all. It rebuilds purely from
data that is intact and self-consistent:

    INITIAL_CAPITAL  (config)
    portfolio.csv    (open positions: ticker, entry date, shares, entry price)
    trades.csv       (closed trades, if any: + exit date/price)

Cash logic mirrors strategy/execution.py exactly:
    buy  : cash -= shares * entry_price                      (no txn cost on buy)
    sell : cash += shares * exit_price * (1 - TRANSACTION_COST)

For every business day from the first entry to today it computes:
    cash(D)            from the entry/exit ledger up to and including D
    portfolio_value(D) = sum(shares * daily_close(ticker, D)) for positions held on D
    total_equity(D)    = cash(D) + portfolio_value(D)

Requires internet (yfinance). Run from the project root:
    python rebuild_equity_history.py
"""

import pandas as pd
import yfinance as yf

try:
    from config import INITIAL_CAPITAL, TRANSACTION_COST
except Exception:
    INITIAL_CAPITAL, TRANSACTION_COST = 100000.0, 0.002

OUT = "data/equity_history.csv"


def build_events():
    """Return a list of entry/exit events from portfolio + trades."""
    events = []

    port = pd.read_csv("data/portfolio.csv")
    for _, r in port.iterrows():
        events.append(dict(
            ticker=r["Ticker"],
            shares=float(r["Shares"]),
            entry_date=pd.to_datetime(r["Entry_Date"]),
            entry_price=float(r["Entry_Price"]),
            exit_date=None,
            exit_price=None,
        ))

    try:
        trades = pd.read_csv("data/trades.csv")
    except FileNotFoundError:
        trades = pd.DataFrame()

    for _, r in trades.iterrows():
        events.append(dict(
            ticker=r["Ticker"],
            shares=float(r["Shares"]),
            entry_date=pd.to_datetime(r["Entry_Date"]),
            entry_price=float(r["Entry_Price"]),
            exit_date=pd.to_datetime(r["Exit_Date"]),
            exit_price=float(r["Exit_Price"]),
        ))

    return events


def fetch_prices(tickers, start, end):
    """Daily close prices, forward-filled across non-trading days."""
    raw = yf.download(
        list(tickers),
        start=start,
        end=end + pd.Timedelta(days=1),
        interval="1d",
        progress=False,
        group_by="ticker",
        auto_adjust=False,
    )

    cols = {}
    for t in tickers:
        try:
            # multi-ticker frames are grouped; single ticker is flat
            s = raw[t]["Close"] if (t in raw.columns.get_level_values(0)) else raw["Close"]
        except Exception:
            s = raw["Close"]
        cols[t] = s

    prices = pd.DataFrame(cols)
    full_idx = pd.date_range(start, end, freq="D")
    return prices.reindex(prices.index.union(full_idx)).sort_index().ffill()


def main():
    events = build_events()
    if not events:
        print("No positions or trades found - nothing to rebuild.")
        return

    tickers = sorted({e["ticker"] for e in events})
    start = min(e["entry_date"] for e in events)
    end = pd.Timestamp.today().normalize()

    print(f"Rebuilding {start.date()} -> {end.date()} for {len(tickers)} tickers ...")
    prices = fetch_prices(tickers, start, end)

    rows = []
    for d in pd.date_range(start, end, freq="D"):
        # only record weekdays (no weekend rows); change to keep all days if wanted
        if d.weekday() >= 5:
            continue

        cash = INITIAL_CAPITAL
        portfolio_value = 0.0

        for e in events:
            if e["entry_date"] <= d:
                cash -= e["shares"] * e["entry_price"]

            exited = e["exit_date"] is not None and e["exit_date"] <= d
            if exited:
                cash += e["shares"] * e["exit_price"] * (1 - TRANSACTION_COST)
            elif e["entry_date"] <= d:
                # still held on day d -> mark to market
                try:
                    px = float(prices.loc[d, e["ticker"]])
                    if pd.notna(px):
                        portfolio_value += e["shares"] * px
                except KeyError:
                    pass

        rows.append(dict(
            Date=d.strftime("%Y-%m-%d"),
            Portfolio_Value=round(portfolio_value, 4),
            Cash=round(cash, 4),
            Total_Equity=round(cash + portfolio_value, 4),
        ))

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"Wrote {len(out)} daily rows to {OUT}")
    print(out.tail(8).to_string(index=False))

    curve = out["Total_Equity"]
    dd = (curve / curve.cummax() - 1) * 100
    print(f"\nStart equity : Rs {curve.iloc[0]:,.2f}")
    print(f"End equity   : Rs {curve.iloc[-1]:,.2f}")
    print(f"Total return : {(curve.iloc[-1]/INITIAL_CAPITAL-1)*100:+.2f}%")
    print(f"Max drawdown : {dd.min():.2f}%")


if __name__ == "__main__":
    main()
