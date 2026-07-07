import pandas as pd
import yfinance as yf

from config import (
    ROE_THRESHOLD,
    PROFIT_MARGIN_THRESHOLD
)

from strategy.indicators import (
    calculate_sma20,
    calculate_volume_sma,
    calculate_momentum_score,
    is_above_sma,
    is_volume_breakout,
    passes_momentum_filter
)


def scan_candidates(
    tickers,
    fundamentals_df,
    week_date
):

    print("Scanning candidates...")

    start_date = (
        pd.Timestamp(week_date)
        - pd.DateOffset(years=1)
    ).strftime("%Y-%m-%d")

    data = yf.download(
        tickers,
        start=start_date,
        end=week_date,
        interval="1wk",
        progress=False
    )

    close_prices = data["Close"]
    high_prices = data["High"]
    volumes = data["Volume"]

    candidates = []

    for t in tickers:

        try:

            if t not in close_prices.columns:
                continue

            df = pd.DataFrame({

                "Close": close_prices[t],
                "High": high_prices[t],
                "Volume": volumes[t]

            }).dropna()

            if len(df) < 30:
                continue

            df["Vol_SMA"] = calculate_volume_sma(df)
            df["SMA20"] = calculate_sma20(df)

            idx = len(df) - 1

            price = float(df["Close"].iloc[idx])
            volume = float(df["Volume"].iloc[idx])

            sma20 = float(df["SMA20"].iloc[idx])
            volume_sma = float(df["Vol_SMA"].iloc[idx])

            score = calculate_momentum_score(df)

            above_sma = is_above_sma(
                price,
                sma20
            )

            volume_breakout = is_volume_breakout(
                volume,
                volume_sma
            )

            momentum_ok = passes_momentum_filter(
                score
            )

            if not above_sma:
                continue

            if not volume_breakout:
                continue

            if not momentum_ok:
                continue

            row = fundamentals_df[
                fundamentals_df["Ticker"] == t
            ]

            if len(row) == 0:
                continue

            margin = row.iloc[0]["Margin"]
            roe = row.iloc[0]["ReturnOnEquity"]

            if pd.isna(margin) or pd.isna(roe):
                continue

            if (
                margin < PROFIT_MARGIN_THRESHOLD
                or
                roe < ROE_THRESHOLD
            ):
                continue

            candidates.append({

                "Ticker": t,

                "Price": price,

                "Score": score,

                "Margin": margin,

                "ROE": roe

            })

        except Exception:

            continue

    candidates.sort(

        key=lambda x: x["Score"],

        reverse=True

    )

    print("\nDEBUG")

    print(
        "Universe:",
        len(tickers)
    )

    print(
        "Candidates:",
        len(candidates)
    )

    return candidates