import time
from datetime import datetime, timedelta
from typing import Iterable, Dict, List

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

    for d in unique_dates:
        if d.weekday() >= 5:
            raise ValueError(f"{d} is not a trading day")

    start = min(unique_dates)
    end = max(unique_dates) + timedelta(days=1)

    attempts = 0
    while True:
        try:
            # yfinance's multi-symbol download function spawns background
            # threads which can easily trigger Yahoo's rate limits. Disable
            # threading and request only the minimal daily data we need.
            df = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                actions=False,
                auto_adjust=False,
                threads=False,
            )
            break
        except YFRateLimitError:
            attempts += 1
            if attempts >= 5:
                raise
            time.sleep(2**attempts)
        except Exception:
            attempts += 1
            if attempts >= 5:
                raise
            time.sleep(1)

    success_count = 0
    for d in unique_dates:
        if (ticker, d) in _PRICE_CACHE:
            continue
        if d not in df.index.date:
            print(f"Yahoo Finance: no price data for {ticker} on {d}")
            continue
        _PRICE_CACHE[(ticker, d)] = round(df.loc[str(d)]["Close"], 2)
        success_count += 1

    print(
        f"Yahoo Finance: retrieved {success_count}/{len(unique_dates)} prices for {ticker}"
    )


def get_price(
    ticker: yf.Ticker,
    date: datetime,
    max_retries: int = 1,
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
        if date.weekday() >= 5:
            raise ValueError(f"{date.date()} is not a trading day")

        attempts = 0
        while True:
            try:
                # Request only one day's OHLC data and disable threads to avoid
                # multiple concurrent connections which can trigger rate limits.
                df = yf.download(
                    ticker.ticker if hasattr(ticker, "ticker") else str(ticker),
                    start=date,
                    end=date + timedelta(days=1),
                    progress=False,
                    actions=False,
                    auto_adjust=False,
                    threads=False,
                )
                break
            except YFRateLimitError:
                attempts += 1
                if attempts > max_retries:
                    raise
                time.sleep(2**attempts)
            except Exception:
                attempts += 1
                if attempts > max_retries:
                    raise
                time.sleep(retry_delay)

        if date not in df.index:
            raise ValueError(
                f"No valid price data found for ticker {ticker.ticker if hasattr(ticker, 'ticker') else str(ticker)} on {date.date()}."
            )

        _PRICE_CACHE[key] = round(df.loc[date]["Close"], 2)
    return _PRICE_CACHE[key]


def download_prices_for_date(
    tickers: Iterable[str], date: datetime.date, retry_delay: float = 1.0
) -> Dict[str, float]:
    """Download closing prices for all ``tickers`` on ``date`` using a single
    :func:`yf.download` call. Values are cached and returned as a mapping.
    """

    uniq = sorted(set(str(t).upper() for t in tickers))
    missing = [t for t in uniq if (t, date) not in _PRICE_CACHE]
    if missing:
        if date.weekday() >= 5:
            raise ValueError(f"{date} is not a trading day")

        attempts = 0
        while True:
            try:
                # Fetch each ticker sequentially with the minimal daily data.
                # yfinance would normally spawn multiple threads when given a
                # list of tickers which increases the risk of HTTP 429 errors.
                df = yf.download(
                    missing,
                    start=date,
                    end=date + timedelta(days=1),
                    progress=False,
                    group_by="ticker",
                    actions=False,
                    auto_adjust=False,
                    threads=False,
                )
                break
            except YFRateLimitError:
                attempts += 1
                if attempts >= 5:
                    raise
                time.sleep(2**attempts)
            except Exception:
                attempts += 1
                if attempts >= 5:
                    raise
                time.sleep(retry_delay)

        for t in missing:
            data = df if len(missing) == 1 else df[t]
            if date not in data.index:
                print(f"Yahoo Finance: no price data for {t} on {date}")
                continue
            price = round(data.loc[date]["Close"], 2)
            _PRICE_CACHE[(t, date)] = price

    return {t: _PRICE_CACHE[(t, date)] for t in uniq}


def download_price(ticker: str, date: datetime.date, retry_delay: float = 1.0) -> float:
    """Convenience wrapper around :func:`download_prices_for_date` for a single ticker."""

    return download_prices_for_date([ticker], date, retry_delay)[ticker]
