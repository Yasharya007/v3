import pandas as pd
import yfinance as yf
from config import (
    POSITION_SIZE,
    TRAILING_STOP,
    TRANSACTION_COST
)
from pandas import Timedelta

def get_total_equity(portfolio, cash):

    portfolio_value = 0

    for _, holding in portfolio.iterrows():

        ticker = holding["Ticker"]
        shares = float(holding["Shares"])

        try:

            data = yf.download(
                ticker,
                period="1d",
                interval="15m",
                progress=False
            )

            if len(data) == 0:
                continue

            current_price = float(
                data["Close"].dropna().iloc[-1].item()
            )

            portfolio_value += (
                shares * current_price
            )

        except:
            continue

    return cash + portfolio_value
def execute_actions():

    actions = pd.read_csv(
        "data/actions.csv"
    )

    if len(actions) == 0:

        print(
            "\nNo actions to execute."
        )

        return
    
    execution_date = (
        pd.to_datetime(
            actions.iloc[0]["Week"]
        )
        +
        pd.Timedelta(days=3)
    ).strftime("%Y-%m-%d")

    portfolio = pd.read_csv(
        "data/portfolio.csv"
    )

    trades = pd.read_csv(
        "data/trades.csv"
    )

    cash = float(

        pd.read_csv(
            "data/capital.csv"
        )["Cash"].iloc[0]

    )

    # -------------------
    # SELLS FIRST
    # -------------------

    sells = actions[
        actions["Action"] == "SELL"
    ]

    for _, row in sells.iterrows():

        ticker = row["Ticker"]

        holding = portfolio[
            portfolio["Ticker"] == ticker
        ]

        if len(holding) == 0:
            continue

        try:

            data = yf.download(
                ticker,
                period="1d",
                interval="15m",
                progress=False
            )

            exit_price = float(data["Close"].dropna().iloc[-1].item())

            shares = float(
                holding["Shares"].iloc[0]
            )

            entry_price = float(
                holding["Entry_Price"].iloc[0]
            )

            cash += (
                shares *
                exit_price* (1 - TRANSACTION_COST)
            )

            pnl = (
                exit_price
                -
                entry_price
            ) * shares

            trade = {

                "Ticker":
                ticker,

                "Entry_Date":
                holding[
                    "Entry_Date"
                ].iloc[0],

                "Exit_Date":
                execution_date,

                "Entry_Price":
                entry_price,

                "Exit_Price":
                exit_price,

                "Shares":
                shares,

                "PnL":
                pnl,

                "Return":
                (
                    (
                        exit_price
                        /
                        entry_price
                    )
                    - 1
                ) * 100,

                "Exit_Reason":
                row["Reason"]

            }

            trades = pd.concat(

                [
                    trades,
                    pd.DataFrame(
                        [trade]
                    )
                ],

                ignore_index=True

            )

            portfolio = portfolio[
                portfolio["Ticker"]
                != ticker
            ]

        except:

            continue

    # -------------------
    # BUYS
    # -------------------
    buys = actions[
        actions["Action"] == "BUY"
    ]
    equity = get_total_equity(
        portfolio,
        cash
    )

    print(
        f"\nCurrent Equity: ₹{equity:,.2f}"
    )

    for _, row in buys.iterrows():

        ticker = row["Ticker"]

        try:

            data = yf.download(
                ticker,
                period="1d",
                interval="15m",
                progress=False
            )

            entry_price = float(
                data["Close"].dropna().iloc[-1].item()
            )

            allocation = (
                equity *
                POSITION_SIZE
            )
            if cash < allocation * 0.80:
                continue
            allocation = min(allocation,cash)
            shares = int(
                allocation
                /
                entry_price
            )

            if shares <= 0:
                continue

            required_cash = (
                shares *
                entry_price
            )

            if required_cash > cash:
                continue

            cash -= required_cash

            new_row = {

                "Ticker":
                ticker,

                "Entry_Date":
                execution_date,

                "Entry_Price":
                entry_price,

                "Shares":
                shares,

                "Trailing_Stop":
                entry_price *
                (
                    1 -
                    TRAILING_STOP
                ),

                "Current_Price":
                entry_price

            }

            portfolio = pd.concat(

                [
                    portfolio,
                    pd.DataFrame(
                        [new_row]
                    )
                ],

                ignore_index=True

            )

        except:

            continue

    portfolio.to_csv(
        "data/portfolio.csv",
        index=False
    )

    trades.to_csv(
        "data/trades.csv",
        index=False
    )

    pd.DataFrame({

        "Cash":
        [cash]

    }).to_csv(

        "data/capital.csv",

        index=False

    )

    print(
        "\nPortfolio updated."
    )