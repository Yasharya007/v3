import pandas as pd
import yfinance as yf
from datetime import timedelta

from config import (
    MAX_POSITIONS,
    POSITION_SIZE,
    TRAILING_STOP,
    MIN_HOLD_WEEKS
)
from strategy.hold_checker import (
    check_hold_conditions
)

# -------------------------
# LOAD / SAVE HELPERS
# -------------------------

def load_portfolio():

    return pd.read_csv(
        "data/portfolio.csv"
    )


def save_portfolio(df):

    df.to_csv(
        "data/portfolio.csv",
        index=False
    )


def load_cash():

    return float(
        pd.read_csv(
            "data/capital.csv"
        )["Cash"].iloc[0]
    )


def save_cash(cash):

    pd.DataFrame({
        "Cash": [cash]
    }).to_csv(
        "data/capital.csv",
        index=False
    )


# -------------------------
# UPDATE EXISTING POSITIONS
# -------------------------

def process_existing_positions():

    portfolio = load_portfolio()

    if len(portfolio) == 0:

        return portfolio, []

    sell_actions = []

    for idx in portfolio.index:

        ticker = portfolio.loc[idx, "Ticker"]

        try:

            data = yf.download(
                ticker,
                period="3mo",
                interval="1wk",
                progress=False
            )

            if len(data) == 0:
                continue

            current_price = float(data["Close"].iloc[-1].item())

            old_stop = float(
                portfolio.loc[idx,
                              "Trailing_Stop"]
            )

            new_stop = max(

                old_stop,

                current_price *
                (1 - TRAILING_STOP)

            )

            portfolio.loc[
                idx,
                "Current_Price"
            ] = current_price

            portfolio.loc[
                idx,
                "Trailing_Stop"
            ] = new_stop

            if current_price <= new_stop:

                sell_actions.append({

                    "Ticker":
                    ticker,

                    "Action":
                    "SELL",

                    "Reason":
                    "Trailing Stop"

                })

        except Exception as e:
            print(f"{ticker}: {e}")
            continue

    return portfolio, sell_actions


# -------------------------
# NEW BUYS
# -------------------------

def generate_buy_actions(pending_sells=0):

    portfolio = load_portfolio()

    current_positions = len(
        portfolio
    )

    slots = (
        MAX_POSITIONS
        -
        current_positions
        +pending_sells
    )

    if slots <= 0:

        return []

    signals = pd.read_csv(
        "data/signals.csv"
    )

    if len(signals) == 0:

        return []

    existing = set()

    if current_positions > 0:

        existing = set(
            portfolio["Ticker"]
        )

    buys = []

    for _, row in signals.iterrows():

        ticker = row["Ticker"]

        if ticker in existing:

            continue

        buys.append({

            "Ticker":
            ticker,

            "Action":
            "BUY",

            "Reason":
            "Signal"

        })

        if len(buys) >= slots:

            break

    return buys

def generate_rotation_actions(
    week_date
):

    portfolio = load_portfolio()

    if len(portfolio) == 0:
        return []

    signals = pd.read_csv(
        "data/signals.csv"
    )
    existing = set(
        portfolio["Ticker"]
    )

    buyable_signals = signals[
        ~signals["Ticker"].isin(existing)
    ]
    if len(buyable_signals) == 0:
        return []

    hold_status = check_hold_conditions(
        portfolio,
        week_date
    )

    rotation_candidates = []

    for _, row in portfolio.iterrows():

        ticker = row["Ticker"]

        if ticker not in hold_status:
            continue

        entry_date = pd.to_datetime(
            row["Entry_Date"]
        )

        holding_weeks = (
            pd.Timestamp(week_date)
            - entry_date
        ).days // 7

        if holding_weeks < MIN_HOLD_WEEKS:
            continue

        status = hold_status[ticker]

        should_hold = (

            status["AboveSMA"]

            or

            status["MomentumOK"]

        )

        if should_hold:
            continue

        rotation_candidates.append({
        
            "Ticker": ticker,
        
            "Score": status["MomentumScore"],
        
            "Action": "SELL",
        
            "Reason": "Rotation"
        
        })

    # Lowest momentum first
    rotation_candidates.sort(
        key=lambda x: x["Score"]
    )

    max_rotation = min(
    len(rotation_candidates),
    len(buyable_signals)
    )

    rotation_sells = []

    for candidate in rotation_candidates[:max_rotation]:

        rotation_sells.append({

            "Ticker": candidate["Ticker"],

            "Action": "SELL",

            "Reason": "Rotation"

        })

    return rotation_sells
# -------------------------
# SAVE ACTIONS
# -------------------------

def save_actions(
    sell_actions,
    buy_actions,
    week_date
):

    actions = []

    for a in sell_actions:

        actions.append({

            "Week":
            week_date,

            **a

        })

    for a in buy_actions:

        actions.append({

            "Week":
            week_date,

            **a

        })

    if len(actions) == 0:

        pd.DataFrame(
            columns=[
                "Week",
                "Ticker",
                "Action",
                "Reason"
            ]
        ).to_csv(
            "data/actions.csv",
            index=False
        )

    else:

        pd.DataFrame(
            actions
        ).to_csv(
            "data/actions.csv",
            index=False
        )

    return actions