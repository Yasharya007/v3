import pandas as pd
from strategy.execution import (
    execute_actions
)
from strategy.equity_tracker import (
    update_equity_history
)
execute_actions()
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
update_equity_history()