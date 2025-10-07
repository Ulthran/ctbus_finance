try:
    from ctbus_finance.sensitive import starting_accounts, starting_investments

    __all__ = ["starting_accounts", "starting_investments"]
except ImportError:
    starting_accounts = set()
    starting_investments = {}
