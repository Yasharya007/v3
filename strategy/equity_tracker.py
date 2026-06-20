"""
equity_tracker.py  (hardened)

Fixes the root cause of the corrupt equity_history.csv:

  1. The old version wrote a row even when every yfinance fetch failed,
     leaving Portfolio_Value / Total_Equity effectively empty. This version
     tracks how many positions were successfully priced and REFUSES to write
     a row unless the whole portfolio was priced -- so a network blip can no
     longer poison the history. It returns/raises instead.

  2. The old "update last row" path did `existing.iloc[-1] = new_row.iloc[0]`,
     which can silently insert NaNs on dtype/column mismatch. This version
     updates by explicit column assignment.

  3. yfinance multi-index / empty frames are handled defensively.
"""

import os
import pandas as pd
import yfinance as yf

FILE_PATH = "data/equity_history.csv"


def _last_close(ticker):
    data = yf.download(
        ticker, period="1d", interval="15m", progress=False, auto_adjust=False
    )
    if data is None or len(data) == 0:
        return None
    close = data["Close"]
    close = close.dropna()
    if len(close) == 0:
        return None
    return float(close.iloc[-1].item())


def update_equity_history():
    portfolio = pd.read_csv("data/portfolio.csv")
    cash = float(pd.read_csv("data/capital.csv")["Cash"].iloc[0])

    portfolio_value = 0.0
    priced = 0
    expected = len(portfolio)

    for _, row in portfolio.iterrows():
        ticker = row["Ticker"]
        shares = float(row["Shares"])
        try:
            price = _last_close(ticker)
            if price is None:
                print("WARN: no price for", ticker)
                continue
            portfolio_value += shares * price
            priced += 1
        except Exception as e:
            print("ERROR:", ticker, e)

    # Refuse to record a misleading row. Either we priced the whole book
    # (expected == priced) or there is genuinely nothing to hold.
    if expected > 0 and priced < expected:
        print(f"Skipping equity write: priced {priced}/{expected} positions. "
              "Fix the price feed and re-run; history left untouched.")
        return False

    total_equity = cash + portfolio_value
    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    new_row = {
        "Date": today,
        "Portfolio_Value": portfolio_value,
        "Cash": cash,
        "Total_Equity": total_equity,
    }

    if os.path.exists(FILE_PATH):
        existing = pd.read_csv(FILE_PATH)
        if len(existing) > 0 and str(existing.iloc[-1]["Date"]) == today:
            for k, v in new_row.items():
                existing.loc[existing.index[-1], k] = v
            existing.to_csv(FILE_PATH, index=False)
        else:
            pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True) \
              .to_csv(FILE_PATH, index=False)
    else:
        pd.DataFrame([new_row]).to_csv(FILE_PATH, index=False)

    print(f"Equity history updated: equity Rs {total_equity:,.2f} "
          f"(cash {cash:,.2f} + holdings {portfolio_value:,.2f})")
    return True


if __name__ == "__main__":
    update_equity_history()