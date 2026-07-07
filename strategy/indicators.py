from config import (
    SCORE_THRESHOLD,
    VOLUME_MULTIPLIER
)


def calculate_sma20(df):

    return (
        df["Close"]
        .rolling(20)
        .mean()
    )


def calculate_volume_sma(df):

    return (
        df["Volume"]
        .rolling(10)
        .mean()
    )


def calculate_momentum_score(df):

    idx = len(df) - 1

    ret_4 = (
        df["Close"].iloc[idx]
        /
        df["Close"].iloc[idx - 4]
    ) - 1

    ret_8 = (
        df["Close"].iloc[idx]
        /
        df["Close"].iloc[idx - 8]
    ) - 1

    ret_12 = (
        df["Close"].iloc[idx]
        /
        df["Close"].iloc[idx - 12]
    ) - 1

    return (

        0.5 * ret_4 +

        0.3 * ret_8 +

        0.2 * ret_12

    )


def is_above_sma(price, sma20):

    return price > sma20


def is_volume_breakout(
    volume,
    volume_sma
):

    return (

        volume

        >

        volume_sma * VOLUME_MULTIPLIER

    )


def passes_momentum_filter(score):

    return score > SCORE_THRESHOLD