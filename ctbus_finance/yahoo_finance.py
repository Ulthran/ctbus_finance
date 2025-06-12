import time
from datetime import datetime, timedelta
from typing import Iterable, Dict

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

# cache to store price lookups so we only hit the network once per
# (ticker, date) pair. This drastically reduces the number of requests
# made to Yahoo Finance which helps avoid hitting rate limits when
# ingesting large CSV files.
_PRICE_CACHE: Dict[tuple[str, datetime.date], float] = {}


def get_ticker_data(ticker: str) -> yf.Ticker:
    """
    Fetches the ticker data from Yahoo Finance.

    Parameters:
    ticker (str): The stock ticker symbol.

    Returns:
    dict: A dictionary containing the ticker data.
    """
    try:
        return yf.Ticker(ticker)
    except Exception as e:
        raise ValueError(f"Error fetching data for ticker {ticker}: {e}")


def get_prices_batch(ticker: str, dates: Iterable[datetime]) -> None:
    """Populate the cache with prices for the given ticker and dates.

    This performs a single Yahoo Finance request for all dates and stores
    the results in ``_PRICE_CACHE``. Subsequent calls to :func:`get_price`
    will use the cached values.

    Parameters
    ----------
    ticker : str
        The asset symbol to fetch.
    dates : Iterable[datetime]
        Collection of dates that need prices.
    """

    unique_dates = sorted({d.date() for d in dates})
    if not unique_dates:
        return

    start = min(unique_dates) - timedelta(days=1)
    end = max(unique_dates) + timedelta(days=2)

    attempts = 0
    while True:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            break
        except YFRateLimitError:
            attempts += 1
            if attempts >= 3:
                raise
            time.sleep(1)
        except Exception:
            attempts += 1
            if attempts >= 3:
                raise
            time.sleep(1)

    success_count = 0
    for d in unique_dates:
        if (ticker, d) in _PRICE_CACHE:
            continue
        subset = df[df.index.date <= d]
        if not subset.empty:
            last_idx = subset.index[-1]
            _PRICE_CACHE[(ticker, d)] = round(subset.loc[last_idx]["Close"], 2)
            success_count += 1

    print(
        f"Yahoo Finance: retrieved {success_count}/{len(unique_dates)} prices for {ticker}"
    )


def get_price(
    ticker: yf.Ticker,
    date: datetime,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> float:
    """
    Fetches the of the given ticker at close for the given date.

    Parameters:
    ticker (Ticker): The stock ticker.
    date (_Date): The date for which to fetch the price.

    Returns:
    float: The price of the ticker.
    """
    key = (ticker.ticker if hasattr(ticker, "ticker") else str(ticker), date.date())
    if key not in _PRICE_CACHE:
        attempts = 0
        while True:
            try:
                df = ticker.history(
                    start=date - timedelta(days=1), end=date + timedelta(days=2)
                )
                break
            except YFRateLimitError:
                attempts += 1
                if attempts >= max_retries:
                    raise
                time.sleep(retry_delay)
            except Exception:
                attempts += 1
                if attempts >= max_retries:
                    raise
                time.sleep(retry_delay)

        if date in df.index:
            _PRICE_CACHE[key] = round(df.loc[date]["Close"], 2)
        else:
            for index in df.index:
                if index.date() <= date.date():
                    _PRICE_CACHE[key] = round(df.loc[index]["Close"], 2)
                    break
            else:
                raise ValueError(
                    f"No valid price data found for ticker {ticker.ticker if hasattr(ticker, 'ticker') else str(ticker)} on or before {date.date()}."
                )
    return _PRICE_CACHE[key]
