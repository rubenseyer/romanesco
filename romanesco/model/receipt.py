from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from typing import Union, Optional, Self
from .lookups import users
from .receipt_formats import parse
from ..util import round, round_even, splits_from_str
from .. import db


def parse_receipt(fp) -> 'Receipt':
    timestamp, comment, items = parse(fp)
    return Receipt(None, timestamp, comment.strip(), list(map(Item.from_parsed, items)), automatic=True)


class Receipt:
    __slots__ = ('id', 'timestamp', 'comment', 'items', 'automatic', '_totals')
    id: int
    timestamp: datetime
    comment: str
    items: list['Item']
    automatic: bool
    _totals: list[Decimal]

    def __init__(self, id, time, comment, items, split_count=None, automatic=False):
        self.id = id
        self.timestamp = time
        self.comment = comment
        self.items = items
        self.automatic = automatic
        self._totals = [Decimal('0') for _ in range(0, (split_count+1) if split_count is not None else (len(users())+1))]
        self.recalculate()

    @staticmethod
    def get(id: int) -> Self:
        c = db.cursor()
        row = c.execute('select timestamp, comment, automatic from receipts where id = ?', (id,)).fetchone()
        if row is None:
            raise LookupError(f'could not find receipt {id}')
        timestamp, comment, automatic = row
        item_rows = list(c.execute('select item_id, name, quantity, price, ean, splits, category_id \
            from receipts_items left join items on item_id = items.id where receipt_id = ? order by sort', (id,)))
        return Receipt(id, datetime.fromtimestamp(timestamp), comment, [Item.from_data(*row) for row in item_rows], automatic=automatic)

    @staticmethod
    def new(time: datetime, comment: str) -> Self:
        # c = db.cursor()
        # row = c.execute('insert into receipts (timestamp, comment) values (?, ?) returning id', (time.timestamp(), comment)).fetchone()
        return Receipt(None, time, comment, [])

    @staticmethod
    def delete(id: int):
        c = db.cursor()
        c.execute('delete from receipts where id = ?', (id,))

    def __str__(self):
        return '\n'.join([self.comment, str(self.timestamp), '=' * 45]
                         + [f'{item.name:<22}{str(item.quantity) + "*" + str(item.price):>15}{item.total():>8}' for item in self.items]
                         + ['=' * 45, str(self.total()).rjust(42)])

    def total(self) -> Decimal:
        return self._totals[0]

    def split_total(self, i: int) -> Decimal:
        return self._totals[i]

    def recalculate(self):
        split_count = len(self._totals) - 1
        self._totals = [Decimal('0') for _ in self._totals]
        for item in self.items:
            self._totals[0] += item.total()
            if item.splits and split_count != len(item.splits):
                raise IndexError('Inconsistent splits across receipt')
            for i in range(1, len(self._totals)):
                self._totals[i] += item.split_total(i, count=split_count)
        self._totals = [round_even(d, prec=Decimal('0.0001')) for d in self._totals]

    def save(self, update_items=True):
        self.recalculate()
        ts = self.timestamp.timestamp()
        with db.transaction():
            c = db.cursor()
            data = (ts, self.comment, ','.join(str(d) for d in self._totals), self.automatic, self.id)
            if self.id is None:
                row = c.execute('insert into receipts (timestamp, comment, cached_totals, automatic) values (?,?,?,?) returning id', data[:-1]).fetchone()
                self.id = row[0]
            else:
                c.execute('update receipts set timestamp = ?, comment = ?, cached_totals = ?, automatic = ? where id = ?', data)
            if not update_items:
                return
            for ix, item in enumerate(self.items):
                if item.id is None:
                    item.find_or_create()
                c.execute('update items set last_use = ? where id = ?', (ts, item.id))
                print((item.id, self.id, item.quantity, item.price, ix))
                c.execute(
                    'insert into receipts_items (item_id, receipt_id, quantity, price, sort) values (?, ?, ?, ?, ?) \
                     on conflict(item_id,receipt_id) do update set quantity = excluded.quantity, price = excluded.price, sort = excluded.sort',
                    (item.id, self.id, item.quantity, item.price, ix))

    def add_item(self, item: 'Item', sort: int):
        if item.splits and len(item.splits) != len(self._totals) - 1:
            raise ValueError('Inconsistent splits across receipt')
        self.items.insert(sort, item)

    def delete_item(self, id: int):
        c = db.cursor()
        c.execute('delete from receipts_items where receipt_id = ? and item_id = ?', (self.id, id))
        self.items = [item for item in self.items if item.id != id]

    def copy(self):
        cls = self.__class__
        new = cls.__new__(cls)
        new.id = self.id
        new.timestamp = self.timestamp
        new.comment = self.comment
        new.items = self.items[:]  # shallow copy
        new._totals = self._totals[:]  # shallow copy
        return new


@dataclass
class Item:
    __slots__ = ('id', 'name', 'quantity', 'price', 'ean', 'splits', 'category')
    id: Optional[int]
    name: str
    quantity: Union[int, Decimal]
    price: Decimal
    ean: Optional[str]
    splits: tuple[int, ...]
    category: int

    @staticmethod
    def from_data(item_id: Optional[int], name: str, quantity: Decimal, price: Decimal, ean: Optional[str], splits: Union[str,tuple[int,...]], category_id: int) -> Self:
        if isinstance(splits, str):
            splits = splits_from_str(splits)
        return Item(item_id, name, quantity, price, ean, splits, category_id)

    @staticmethod
    def get(item_id: int, quantity: Decimal, price: Decimal) -> Self:
        c = db.cursor()
        name, ean, splits, category_id = c.execute('select name, ean, splits, category_id from items where id = ? ', (item_id,)).fetchone()
        return Item.from_data(item_id, name, quantity, price, ean, splits, category_id)

    @staticmethod
    def from_parsed(raw) -> Self:
        c = db.cursor()
        name, quantity, price, ean = raw
        item_id = None
        splits = ''
        category_id = None
        # First try to lookup based on EAN
        if ean is not None:
            row = c.execute('select id, splits, category_id from items where ean = ? order by last_use desc, id desc limit 1', (ean,)).fetchone()
            if row is not None:
                item_id, splits, category_id = row
        # If EAN lookup fails, try to lookup based on name
        if category_id is None:
            row = c.execute('select id, splits, category_id from items where name = ? order by last_use desc, id desc limit 1', (name,)).fetchone()
            if row is not None:
                item_id, splits, category_id = row
        return Item.from_data(item_id, name, quantity, price, ean, splits, category_id)

    def find_or_create(self) -> None:
        if self.id is not None:
            raise ValueError('item already registered')
        if self.category is None:  # unseen item in automatic
            self.category = 1
        splits = ','.join(str(s) for s in self.splits)
        c = db.cursor()
        candidate = c.execute('select id from items where name = ? and (ean is not distinct from ?) and splits = ? and category_id = ?',
                              (self.name, self.ean, splits, self.category)).fetchone()
        if candidate is None:
            candidate = c.execute('insert into items (name, ean, splits, category_id) values (?,?,?,?) returning id',
                                  (self.name, self.ean, splits, self.category)).fetchone()
        self.id = candidate[0]
        c.close()  # Eager close required since we may not read all candidate rows.

    def total(self) -> Decimal:
        return round(self.quantity * self.price)

    def split_total(self, i: int, count=1) -> Decimal:
        if not self.splits:
            return self.total() / count
        return (self.total() * self.splits[i-1]) / sum(self.splits)
