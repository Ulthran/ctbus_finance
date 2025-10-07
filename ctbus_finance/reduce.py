from beancount.core.position import Position
from decimal import Decimal
from collections import deque


def reduce_fifo(positions: list[Position]) -> list[Position]:
    """
    Reduce a list of beancount.core.position.Position objects using FIFO logic.

    Args:
        positions (list[Position]): Sequence of buy/sell positions.
            Positive units = acquisitions
            Negative units = disposals

    Returns:
        list[Position]: Remaining open positions (lots) after FIFO reduction.
    """
    fifo = deque()
    for pos in positions:
        qty = pos.units.number

        if qty > 0:
            # Add a new lot to FIFO queue
            fifo.append(pos)
        elif qty < 0:
            sell_qty = -qty
            while sell_qty > 0 and fifo:
                buy = fifo[0]
                buy_qty = buy.units.number

                if buy_qty <= sell_qty:
                    # Entire buy lot consumed
                    sell_qty -= buy_qty
                    fifo.popleft()
                else:
                    # Partial consumption of buy lot
                    remaining_qty = buy_qty - sell_qty
                    fifo[0] = Position(
                        buy.units._replace(number=remaining_qty), buy.cost
                    )
                    sell_qty = Decimal("0")

    return list(fifo)
