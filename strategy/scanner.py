import pandas as pd
import numpy as np
import yfinance as yf

from config import (
    ROE_THRESHOLD,
    SCORE_THRESHOLD,
    VOLUME_MULTIPLIER,
    PROFIT_MARGIN_THRESHOLD
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

                "Close":
                close_prices[t],

                "High":
                high_prices[t],

                "Volume":
                volumes[t]

            }).dropna()

            if len(df) < 30:
                continue

            df["Vol_SMA"] = (
                df["Volume"]
                .rolling(10)
                .mean()
            )

            df["SMA20"] = (df["Close"].rolling(20).mean())

            idx = len(df) - 1

            price = float(
                df["Close"].iloc[idx]
            )

            vol = float(
                df["Volume"].iloc[idx]
            )

            vol_sma = float(
                df["Vol_SMA"].iloc[idx]
            )
            sma20 = float(
                df["SMA20"].iloc[idx]
            )
            if (
                price >sma20
            ):

                if (
                    vol >
                    vol_sma *
                    VOLUME_MULTIPLIER
                ):

                    ret_4 = (
                        price /
                        float(
                            df["Close"]
                            .iloc[idx-4]
                        )
                    ) - 1

                    ret_8 = (
                        price /
                        float(
                            df["Close"]
                            .iloc[idx-8]
                        )
                    ) - 1

                    ret_12 = (
                        price /
                        float(
                            df["Close"]
                            .iloc[idx-12]
                        )
                    ) - 1

                    score = (

                        0.5 * ret_4 +

                        0.3 * ret_8 +

                        0.2 * ret_12

                    )

                    if (
                        score <=
                        SCORE_THRESHOLD
                    ):
                        continue

                    row = fundamentals_df[
                        fundamentals_df["Ticker"]
                        == t
                    ]

                    if len(row) == 0:
                        continue

                    margin = (
                        row.iloc[0]["Margin"]
                    )

                    roe = (
                        row.iloc[0]["ReturnOnEquity"]  
                    )
                    if pd.isna(margin):
                        continue
                    if pd.isna(roe):
                        continue
                    if (
                        margin <
                        PROFIT_MARGIN_THRESHOLD or roe < ROE_THRESHOLD
                    ):
                        continue

                    candidates.append({

                        "Ticker":
                        t,

                        "Price":
                        price,

                        "Score":
                        score,

                        "Margin":
                        margin,
                        "ROE":
                        roe

                    })

        except:

            continue

    candidates = sorted(

        candidates,

        key=lambda x:
        x["Score"],

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