from config import (
    SCORE_THRESHOLD,
    VOLUME_MULTIPLIER
)


def get_technical_metrics(df):

    idx = len(df) - 1

    price = float(
        df["Close"].iloc[idx]
    )

    volume = float(
        df["Volume"].iloc[idx]
    )

    sma20 = (
        df["Close"]
        .rolling(20)
        .mean()
        .iloc[idx]
    )

    volume_sma = (
        df["Volume"]
        .rolling(10)
        .mean()
        .iloc[idx]
    )

    ret_4 = (
        price /
        float(df["Close"].iloc[idx - 4])
    ) - 1

    ret_8 = (
        price /
        float(df["Close"].iloc[idx - 8])
    ) - 1

    ret_12 = (
        price /
        float(df["Close"].iloc[idx - 12])
    ) - 1

    momentum_score = (

        0.5 * ret_4 +

        0.3 * ret_8 +

        0.2 * ret_12

    )

    return {

        "Price": price,

        "Volume": volume,

        "SMA20": float(sma20),

        "VolumeSMA": float(volume_sma),

        "AboveSMA": (
            price > sma20
        ),

        "VolumeBreakout": (
            volume >
            volume_sma *
            VOLUME_MULTIPLIER
        ),

        "MomentumScore":
        momentum_score,

        "MomentumOK":
        momentum_score >
        SCORE_THRESHOLD

    }