import pandas as pd
import yfinance as yf

from strategy.indicators import (
    get_technical_metrics
)


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

    volumes = data["Volume"]

    results = {}

    for ticker in tickers:

        try:

            if ticker not in close_prices.columns:
                continue

            df = pd.DataFrame({

                "Close":
                close_prices[ticker],

                "Volume":
                volumes[ticker]

            }).dropna()

            if len(df) < 30:
                continue

            results[ticker] = (
                get_technical_metrics(df)
            )

        except Exception:

            continue

    return results