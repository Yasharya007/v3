import yfinance as yf
from yfinance import EquityQuery

def get_universe(start_rank, end_rank):

    query = EquityQuery(
        'is-in',
        ['exchange', 'NSI']
    )

    response = yf.screen(
        query,
        sortField='intradaymarketcap',
        sortAsc=False,
        size=250
    )

    quotes = response.get('quotes', [])

    tickers = [
        q['symbol']
        for q in quotes
    ]

    return tickers[start_rank:end_rank]