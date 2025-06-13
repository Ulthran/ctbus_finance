"""Helper functions for retrieving prices from Yahoo Finance.

This module provides a thin wrapper around :mod:`yfinance` that caches
responses and tries to minimise the number of requests in order to avoid
hitting Yahoo's rate limits.  Only a subset of the larger module that used to
live here is implemented as we really only need bulk daily price lookups when
ingesting account holdings.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Dict, Iterable, List

from curl_cffi import requests as curl_requests
import pandas as pd

from ctbus_finance.db import get_session
from ctbus_finance.models import PriceCache

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)

# Cache of {(ticker, date): price}.  Prices are stored rounded to two decimal
# places to avoid small floating point differences from yfinance.
_PRICE_CACHE: Dict[tuple[str, date], float] = {}

# How many tickers to fetch per Yahoo Finance request.  Smaller batches help
# avoid rate limiting when requesting many symbols at once.
_BATCH_SIZE = 10

# Seconds to wait between batches
_BATCH_DELAY = 1.0

# Use a single session with a consistent User-Agent to avoid Yahoo rate
# limiting triggered by fingerprint changes.
_SESSION = curl_requests.Session(impersonate="chrome")


def download_prices_for_date(
    tickers: Iterable[str], on_date: date, max_retries: int = 8
) -> Dict[str, float]:
    """Return closing prices for ``tickers`` on ``on_date``.

    ``yfinance.download`` normally spawns several threads which can easily hit
    Yahoo's rate limits when requesting data for many symbols.  To keep things
    simple and predictable we fetch all tickers in a single request with
    ``threads=False`` and retry a few times if we encounter ``YFRateLimitError``.
    Results are cached so repeated calls for the same ticker/date pair do not
    trigger additional network requests.
    """

    unique = sorted({t.upper() for t in tickers})
    logger.debug("Fetching prices for %s on %s", unique, on_date)

    session = get_session()
    missing: List[str] = []
    for t in unique:
        if (t, on_date) in _PRICE_CACHE:
            continue
        cached = session.query(PriceCache).filter_by(symbol=t, date=on_date).first()
        if cached:
            _PRICE_CACHE[(t, on_date)] = cached.price
        else:
            missing.append(t)

    if missing:
        logger.debug("Missing from cache: %s", missing)
    if missing:
        if on_date.weekday() >= 5:
            session.close()
            raise ValueError(f"{on_date} is not a trading day")

        for i in range(0, len(missing), _BATCH_SIZE):
            batch = missing[i : i + _BATCH_SIZE]
            attempts = 0
            while True:
                try:
                    df = yf.download(
                        batch,
                        start=on_date,
                        end=on_date + timedelta(days=1),
                        progress=False,
                        group_by="ticker",
                        actions=False,
                        auto_adjust=False,
                        threads=False,
                        session=_SESSION,
                    )
                    logger.debug("Fetched data for %s on %s", batch, on_date)
                    break
                except YFRateLimitError:
                    attempts += 1
                    logger.warning(
                        "Rate limited fetching %s on %s (attempt %d)",
                        batch,
                        on_date,
                        attempts,
                    )
                    if attempts >= max_retries:
                        session.close()
                        raise
                    time.sleep(2**attempts)
                except Exception as exc:
                    attempts += 1
                    logger.warning(
                        "Error fetching %s on %s: %s (attempt %d)",
                        batch,
                        on_date,
                        exc,
                        attempts,
                    )
                    if attempts >= max_retries:
                        session.close()
                        raise
                    time.sleep(1)

            for t in batch:
                try:
                    data = df if len(batch) == 1 else df[t]
                    if len(batch) == 1 and isinstance(df.columns, pd.MultiIndex):
                        if t in df.columns.get_level_values(0):
                            data = df[t]
                        elif t in df.columns.get_level_values(-1):
                            data = df.xs(t, level=-1, axis=1)
                    idx_no_tz = (
                        data.index.tz_localize(None) if data.index.tz else data.index
                    )
                    if pd.Timestamp(on_date) not in idx_no_tz:
                        continue
                    loc = data.index[idx_no_tz.get_loc(pd.Timestamp(on_date))]
                    price = round(float(data.loc[loc]["Close"]), 2)
                except Exception as exc:  # noqa: PERF203
                    logger.warning(
                        "Failed to fetch price for %s on %s: %s", t, on_date, exc
                    )
                    continue

                _PRICE_CACHE[(t, on_date)] = price
                session.merge(PriceCache(symbol=t, date=on_date, price=price))
                logger.debug("Cached price for %s on %s: %s", t, on_date, price)

            session.commit()
            time.sleep(_BATCH_DELAY)

    session.close()

    result = {
        t: _PRICE_CACHE[(t, on_date)] for t in unique if (t, on_date) in _PRICE_CACHE
    }
    logger.debug("Returning prices: %s", result)
    return result


def download_price(ticker: str, on_date: date) -> float:
    """Convenience wrapper for :func:`download_prices_for_date`."""

    prices = download_prices_for_date([ticker], on_date)
    if ticker.upper() not in prices:
        raise ValueError(f"No price data for {ticker} on {on_date}")
    return prices[ticker.upper()]


def clear_cache() -> None:
    """Remove all cached price data."""

    _PRICE_CACHE.clear()
    session = get_session()
    session.query(PriceCache).delete()
    session.commit()
    session.close()
    logger.debug("Price cache cleared")
