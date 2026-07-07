import pandas as pd
import yfinance as yf

from config import SCORE_THRESHOLD


def check_hold_conditions(
    portfolio,
    week_date
):

    if len(portfolio) == 0:
        return {}

    tickers = portfolio["Ticker"].tolist()

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

    hold_status = {}

    for ticker in tickers:

        try:

            if ticker not in close_prices.columns:
                continue

            df = pd.DataFrame({

                "Close": close_prices[ticker]

            }).dropna()

            if len(df) < 30:
                continue

            df["SMA20"] = (
                df["Close"]
                .rolling(20)
                .mean()
            )

            idx = len(df) - 1

            price = float(
                df["Close"].iloc[idx]
            )

            sma20 = float(
                df["SMA20"].iloc[idx]
            )

            above_sma = (
                price > sma20
            )

            ret_4 = (
                price /
                float(df["Close"].iloc[idx-4])
            ) - 1

            ret_8 = (
                price /
                float(df["Close"].iloc[idx-8])
            ) - 1

            ret_12 = (
                price /
                float(df["Close"].iloc[idx-12])
            ) - 1

            score = (

                0.5 * ret_4 +

                0.3 * ret_8 +

                0.2 * ret_12

            )

            momentum_ok = (
                score > SCORE_THRESHOLD
            )

            hold_status[ticker] = {

                "Price": price,

                "AboveSMA": above_sma,

                "MomentumScore": score,

                "MomentumOK": momentum_ok

            }

        except Exception:

            continue

    return hold_status