import morningstar_data as md


def get_allocation_morningstar(ticker):
    try:
        fund = MorningstarFund(ticker)
        allocation = fund.asset_allocation()
        style_box = fund.equity_style_box()

        result = {
            "fund_name": fund.name,
            "ticker": ticker,
            "category": fund.category,
            "large_cap": style_box.get("Large", 0),
            "mid_cap": style_box.get("Mid", 0),
            "small_cap": style_box.get("Small", 0),
            "international": allocation.get("foreign_stock", 0),
            "cash": allocation.get("cash", 0),
            "bonds": allocation.get("bond", 0),
            "other": allocation.get("other", 0),
        }

        return result
    except Exception as e:
        print(f"Error retrieving data for {ticker}: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Replace 'VEXAX' with the desired ticker symbol
    data = get_allocation_morningstar("VEXAX")
    print(data)
