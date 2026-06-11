from datetime import datetime
from strategy.portfolio_manager import (
    process_existing_positions,
    generate_buy_actions,
    save_actions,save_portfolio
)
from strategy.system_state import (
    already_processed,
    save_processed
)
from strategy.universe import (
    get_universe
)

from strategy.fundamentals import (
    build_fundamental_cache
)

from strategy.scanner import (
    scan_candidates
)

from config import (
    UNIVERSE_START,
    UNIVERSE_END
)

today = datetime.today()

week_date = today.strftime(
    "%Y-%m-%d"
)
if already_processed(
    week_date
):

    print(
        "\nThis week "
        "has already been processed."
    )

    exit()
print(
    f"\nRunning Weekly Scan: "
    f"{week_date}\n"
)

tickers = get_universe(

    UNIVERSE_START,

    UNIVERSE_END

)

fundamentals = (
    build_fundamental_cache(
        tickers
    )
)

candidates = scan_candidates(

    tickers,

    fundamentals,

    week_date

)
import pandas as pd

signals_df = pd.DataFrame(candidates)

signals_df.to_csv(
    "data/signals.csv",
    index=False
)
print(
    f"\nSaved "
    f"{len(signals_df)} "
    f"signals to data/signals.csv"
)
portfolio, sells = (
    process_existing_positions()
)
save_portfolio(portfolio)
buys = (
    generate_buy_actions()
)

actions = save_actions(

    sells,

    buys,

    week_date

)

print("\nACTIONS\n")

for a in actions:

    print(

        a["Action"],

        a["Ticker"],

        "-",

        a["Reason"]

    )
print("\nTOP CANDIDATES\n")
print(
    "\nTotal Candidates:",
    len(candidates)
)
for i, c in enumerate(candidates, start=1):

    print(
        f"{i}. "
        f"{c['Ticker']} | "
        f"Score={c['Score']:.4f} | "
        f"Margin={c['Margin']*100:.2f}% | "
        f"ROE={c['ROE']*100:.2f}% | "
        f"Price={c['Price']:.2f}"
    )
save_processed(
    week_date
)
