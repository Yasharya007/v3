import pandas as pd
import yfinance as yf
import os


def update_equity_history():

    portfolio = pd.read_csv(
        "data/portfolio.csv"  
    )

    cash = float(

        pd.read_csv(
            "data/capital.csv"
        )["Cash"].iloc[0]

    )

    portfolio_value = 0

    for _, row in portfolio.iterrows():

        ticker = row["Ticker"]

        shares = float(
            row["Shares"]
        )

        try:

            data = yf.download(
                ticker,
                period="1mo",
                interval="1wk",
                progress=False
            )

            if len(data) == 0:
                continue

            price = float(
                data["Close"].iloc[-1].item()
            )

            portfolio_value += (
                shares * price
            )

        except:

            continue

    total_equity = (

        cash
        +
        portfolio_value

    )

    today = pd.Timestamp.today(
    ).strftime("%Y-%m-%d")

    new_row = pd.DataFrame([{

        "Date":
        today,

        "Portfolio_Value":
        portfolio_value,

        "Cash":
        cash,

        "Total_Equity":
        total_equity

    }])

    file_path = (
        "data/equity_history.csv"
    )

    if os.path.exists(
        file_path
    ):

        existing = pd.read_csv(
            file_path
        )

        if (
            len(existing) > 0
            and
            existing.iloc[-1]["Date"]
            == today
        ):

            existing.iloc[-1] = (
                new_row.iloc[0]
            )

            existing.to_csv(
                file_path,
                index=False
            )

            return

        pd.concat(

            [
                existing,
                new_row
            ],

            ignore_index=True

        ).to_csv(

            file_path,

            index=False

        )

    else:

        new_row.to_csv(

            file_path,

            index=False

        )

    print(
        "\nEquity history updated."
    )