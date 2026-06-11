import pandas as pd
import yfinance as yf

portfolio = pd.read_csv(
    "data/portfolio.csv"
)

if len(portfolio) == 0:
    print("Portfolio empty")
    exit()

for idx in portfolio.index:

    ticker = portfolio.loc[idx, "Ticker"]

    try:

        data = yf.download(
            ticker,
            period="5d",
            interval="1d",
            progress=False
        )

        current_price = float(
            data["Close"].iloc[-1].item()
        )

        portfolio.loc[
            idx,
            "Current_Price"
        ] = current_price

    except:

        continue

portfolio["Invested_Value"] = (
    portfolio["Entry_Price"]
    *
    portfolio["Shares"]
)

portfolio["Current_Value"] = (
    portfolio["Current_Price"]
    *
    portfolio["Shares"]
)

portfolio["PnL"] = (
    portfolio["Current_Value"]
    -
    portfolio["Invested_Value"]
)

portfolio["Return_%"] = (
    (
        portfolio["Current_Value"]
        /
        portfolio["Invested_Value"]
    )
    - 1
) * 100

portfolio.to_csv(
    "data/portfolio.csv",
    index=False
)

print("Portfolio updated.")