import pandas as pd
import yfinance as yf


# --------------------------------------------------
# CALCULATE ROE FROM ANNUAL FINANCIAL STATEMENTS
# --------------------------------------------------

def calculate_roe_from_financials(ticker):

    try:

        income = ticker.income_stmt
        balance = ticker.balance_sheet

        if income.empty or balance.empty:
            return None

        # Find annual periods available in both statements
        common_dates = (
            income.columns
            .intersection(balance.columns)
        )

        common_dates = sorted(
            common_dates,
            reverse=True
        )

        # Need current and previous year
        if len(common_dates) < 2:
            return None

        current_date = common_dates[0]
        previous_date = common_dates[1]

        # ------------------------------------------
        # Net Income
        # ------------------------------------------

        if "Net Income" not in income.index:
            return None

        net_income = income.loc[
            "Net Income",
            current_date
        ]

        # ------------------------------------------
        # Stockholders Equity
        # ------------------------------------------

        if "Stockholders Equity" not in balance.index:
            return None

        current_equity = balance.loc[
            "Stockholders Equity",
            current_date
        ]

        previous_equity = balance.loc[
            "Stockholders Equity",
            previous_date
        ]

        # ------------------------------------------
        # Validate values
        # ------------------------------------------

        if pd.isna(net_income):
            return None

        if pd.isna(current_equity):
            return None

        if pd.isna(previous_equity):
            return None

        # ------------------------------------------
        # Average shareholders' equity
        # ------------------------------------------

        average_equity = (
            float(current_equity)
            +
            float(previous_equity)
        ) / 2

        if average_equity == 0:
            return None

        # ------------------------------------------
        # ROE
        # ------------------------------------------

        roe = (
            float(net_income)
            /
            average_equity
        )

        return roe

    except Exception as e:

        print(
            f"ROE calculation error: {e}"
        )

        return None


# --------------------------------------------------
# BUILD FUNDAMENTAL CACHE
# --------------------------------------------------

def build_fundamental_cache(tickers):

    print(
        "\nBuilding fundamental cache..."
    )

    records = []

    for t in tickers:

        # print(
        #     f"Fetching fundamentals: {t}"
        # )

        try:

            ticker = yf.Ticker(t)

            info = ticker.info

            # --------------------------------------
            # Profit Margin
            # --------------------------------------

            margin = info.get(
                "profitMargins"
            )

            # --------------------------------------
            # Yahoo reported ROE
            # --------------------------------------

            yahoo_roe = info.get(
                "returnOnEquity"
            )

            # --------------------------------------
            # ROE fallback
            # --------------------------------------

            if (
                yahoo_roe is not None
                and not pd.isna(yahoo_roe)
            ):

                roe = float(
                    yahoo_roe
                )

                roe_source = "Yahoo"

            else:

                roe = (
                    calculate_roe_from_financials(
                        ticker
                    )
                )

                if roe is not None:

                    roe_source = "Calculated"

                else:

                    roe_source = "Unavailable"

            records.append({

                "Ticker":
                t,

                "Margin":
                margin,

                "ReturnOnEquity":
                roe,

                "ROE_Source":
                roe_source

            })

            # print(
            #     f"  Margin={margin} | "
            #     f"ROE={roe} | "
            #     f"Source={roe_source}"
            # )

        except Exception as e:

            # print(
            #     f"  ERROR: {e}"
            # )

            records.append({

                "Ticker":
                t,

                "Margin":
                None,

                "ReturnOnEquity":
                None,

                "ROE_Source":
                "Unavailable"

            })

    fundamentals_df = pd.DataFrame(
        records
    )

    fundamentals_df.to_csv(
        "data/fundamentals_cache.csv",
        index=False
    )

    print(
        "\nFundamental cache saved."
    )

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    print(
        "\nROE SOURCE SUMMARY"
    )

    print(
        fundamentals_df[
            "ROE_Source"
        ].value_counts(
            dropna=False
        )
    )

    return fundamentals_df