from decimal import Decimal
from .receipts import load_receipt as load_receipt_raw, Receipt, Item


def load_receipt(fp, c: 'db.Cursor') -> 'SplitReceipt':
    sr = SplitReceipt(load_receipt_raw(fp), c)
    return sr


class SplitReceipt:
    __slots__ = ('receipt', 'splits', '_total_split', '_split_count')
    receipt: Receipt
    splits: list[tuple[int, ...]]

    def __init__(self, receipt: Receipt, c: 'db.Cursor'):
        self.receipt = receipt
        # TODO with db to set self.splits
        # Check that splits are consistent
        if any(s and len(s) != self._split_count for s in self.splits):
            raise IndexError('Inconsistent splits across receipt')

    def items_splits(self):
        return zip(self.receipt.items, self.splits)

    def total(self):
        return self.receipt.total()

    def total_split(self) -> list[Decimal, ...]:
        return self._total_split

    def recalculate(self):
        self.receipt.recalculate()
        # Compensate for rounding
        rounding = (self.total() - self.receipt._total) / self._split_count
        self._total_split = \
            [sum(item.quantity * _split_price(item, self.splits[j], i) for j, item in enumerate(self.receipt.items)) + rounding
             for i in range(0, self._split_count)]


def _split_price(item: Item, split: tuple[int, ...], i: int) -> Decimal:
    if not split:
        return item.price
    return (item.price * split[i]) / sum(split)
