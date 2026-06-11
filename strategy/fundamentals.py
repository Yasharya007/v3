import yfinance as yf
import pandas as pd

def build_fundamental_cache(tickers):

    records = []

    for t in tickers:

        try:

            info = yf.Ticker(t).info

            records.append({

                "Ticker": t,

                "Margin":
                info.get("profitMargins"),
                "ReturnOnEquity": info.get("returnOnEquity")

            })

        except:

            pass

    df = pd.DataFrame(records)

    df.to_csv(
        "data/fundamentals_cache.csv",
        index=False
    )

    return df