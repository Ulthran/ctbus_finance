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
from typing import Dict, Iterable

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)

# Cache of {(ticker, date): price}.  Prices are stored rounded to two decimal
# places to avoid small floating point differences from yfinance.
_PRICE_CACHE: Dict[tuple[str, date], float] = {}


def download_prices_for_date(
    tickers: Iterable[str], on_date: date, max_retries: int = 5
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
    missing = [t for t in unique if (t, on_date) not in _PRICE_CACHE]
    if missing:
        logger.debug("Missing from cache: %s", missing)
    if missing:
        if on_date.weekday() >= 5:
            # Markets are closed on weekends
            raise ValueError(f"{on_date} is not a trading day")

        attempts = 0
        while True:
            try:
                df = yf.download(
                    missing,
                    start=on_date,
                    end=on_date + timedelta(days=1),
                    progress=False,
                    group_by="ticker",
                    actions=False,
                    auto_adjust=False,
                    threads=False,
                )
                logger.debug("Fetched data for %s on %s", missing, on_date)
                break
            except YFRateLimitError:
                attempts += 1
                logger.warning(
                    "Rate limited fetching %s on %s (attempt %d)",
                    missing,
                    on_date,
                    attempts,
                )
                if attempts >= max_retries:
                    raise
                time.sleep(2**attempts)
            except Exception as exc:
                attempts += 1
                logger.warning(
                    "Error fetching %s on %s: %s (attempt %d)",
                    missing,
                    on_date,
                    exc,
                    attempts,
                )
                if attempts >= max_retries:
                    raise
                time.sleep(1)

        for t in missing:
            data = df if len(missing) == 1 else df[t]
            if on_date not in data.index:
                # Yahoo occasionally omits prices (holidays etc.).  Skip silently.
                continue
            price = round(float(data.loc[on_date]["Close"]), 2)
            _PRICE_CACHE[(t, on_date)] = price
            logger.debug("Cached price for %s on %s: %s", t, on_date, price)

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
    logger.debug("Price cache cleared")
