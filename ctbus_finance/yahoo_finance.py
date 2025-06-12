import time
from datetime import datetime, timedelta

import yfinance as yf
from yfinance.exceptions import YFRateLimitError


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
        return round(df.loc[date]["Close"], 2)
    else:
        # Iterate through the DataFrame and return the first available price
        for index in df.index:
            if index.date() <= date.date():
                return round(df.loc[index]["Close"], 2)
