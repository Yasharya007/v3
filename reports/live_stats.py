import pandas as pd


def print_live_stats():

    # -------------------
    # LOAD FILES
    # -------------------

    equity_df = pd.read_csv(
        "data/equity_history.csv"
    )

    portfolio_df = pd.read_csv(
        "data/portfolio.csv"
    )

    trades_df = pd.read_csv(
        "data/trades.csv"
    )

    cash = float(
        pd.read_csv(
            "data/capital.csv"
        )["Cash"].iloc[0]
    )

    # -------------------
    # CURRENT EQUITY
    # -------------------

    current_equity = float(
        equity_df[
            "Total_Equity"
        ].iloc[-1]
    )

    starting_equity = float(
        equity_df[
            "Total_Equity"
        ].iloc[0]
    )

    total_return = (

        (
            current_equity
            /
            starting_equity
        )
        - 1

    ) * 100

    # -------------------
    # CAGR
    # -------------------

    if len(equity_df) > 1:

        start_date = pd.to_datetime(
            equity_df["Date"].iloc[0]
        )

        end_date = pd.to_datetime(
            equity_df["Date"].iloc[-1]
        )

        years = (

            (
                end_date
                -
                start_date
            ).days

            / 365.25

        )

        if years > 0:

            cagr = (

                (
                    current_equity
                    /
                    starting_equity
                )

                **

                (
                    1 / years
                )

                - 1

            ) * 100

        else:

            cagr = 0

    else:

        cagr = 0

    # -------------------
    # DRAWDOWN
    # -------------------

    equity_series = equity_df[
        "Total_Equity"
    ]

    rolling_max = (
        equity_series.cummax()
    )

    drawdown = (

        equity_series
        /
        rolling_max

        - 1

    ) * 100

    max_drawdown = drawdown.min()

    # -------------------
    # TRADE STATS
    # -------------------

    trade_count = len(
        trades_df
    )

    if trade_count > 0:

        winners = trades_df[
            trades_df["PnL"] > 0
        ]

        win_rate = (

            len(winners)

            /

            trade_count

        ) * 100

    else:

        win_rate = 0

    # -------------------
    # PORTFOLIO VALUE
    # -------------------

    invested = (

        current_equity
        -
        cash

    )

    # -------------------
    # OUTPUT
    # -------------------

    print(
        "\n===== LIVE PORTFOLIO ====="
    )

    print(
        f"\nCurrent Equity: "
        f"₹{current_equity:,.2f}"
    )

    print(
        f"Cash: "
        f"₹{cash:,.2f}"
    )

    print(
        f"Invested: "
        f"₹{invested:,.2f}"
    )

    print(
        f"Open Positions: "
        f"{len(portfolio_df)}"
    )

    print(
        f"\nTotal Return: "
        f"{total_return:.2f}%"
    )

    print(
        f"CAGR: "
        f"{cagr:.2f}%"
    )

    print(
        f"Maximum Drawdown: "
        f"{max_drawdown:.2f}%"
    )

    print(
        f"\nClosed Trades: "
        f"{trade_count}"
    )

    print(
        f"Win Rate: "
        f"{win_rate:.2f}%"
    )


if __name__ == "__main__":

    print_live_stats()