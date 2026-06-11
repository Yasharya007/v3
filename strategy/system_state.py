import pandas as pd
import os


def already_processed(run_date):

    if not os.path.exists(
        "data/system_state.csv"
    ):
        return False

    df = pd.read_csv(
        "data/system_state.csv"
    )

    if len(df) == 0:
        return False

    return (
        str(
            df.iloc[0]["Last_Run_Date"]
        )
        ==
        str(run_date)
    )


def save_processed(run_date):

    pd.DataFrame({

        "Last_Run_Date":
        [run_date]

    }).to_csv(

        "data/system_state.csv",

        index=False

    )