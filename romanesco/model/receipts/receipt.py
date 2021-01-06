from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from typing import Union, Optional
from .util import round
from .formats import parse


def load_receipt(fp) -> 'Receipt':
    timestamp, items = parse(fp)
    return Receipt(timestamp, [Item(n, q, p, ean=e) for n,q,p,e in items])


class Receipt:
    __slots__ = ('timestamp', 'items', '_total', '_total_split')
    timestamp: datetime
    items: list['Item']

    def __init__(self, time, items):
        self.timestamp = time
        self.items = items
        self.recalculate()

    def __str__(self):
        return '\n'.join([str(self.timestamp), '=' * 45]
                         + [f'{item.name:<22}{str(item.quantity) + "*" + str(item.price):>15}{round(item.quantity*item.price):>8}' for item in self.items]
                         + ['=' * 45, str(self.total()).rjust(42)])

    def total(self) -> Decimal:
        return round(self._total)

    def recalculate(self):
        self._total = sum(item.quantity * item.price for item in self.items)


@dataclass
class Item:
    __slots__ = ('name', 'quantity', 'price', 'ean')
    name: str
    quantity: Union[int, Decimal]
    price: Decimal
    ean: Optional[str]

    def __init__(self, name: str, quantity: Union[int, Decimal], price: Decimal, ean=None):
        self.name = name
        self.quantity = quantity
        self.price = price
        self.ean = ean
