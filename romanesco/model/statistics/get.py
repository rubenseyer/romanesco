from datetime import datetime, timedelta
from decimal import Decimal
from math import floor
from typing import Optional
from itertools import groupby

from ...util import dense
from .update import period
from .util_dateocc import date_occurrences

from ... import app
from .. import db
from ..receipt import Item


def stats_overview(user_id: int):
    c = db.cursor()
    today = datetime.today()

    # Net and target
    row = c.execute('select net, target from users where id = ?', (user_id,)).fetchone()
    if row is None:
        raise LookupError(f'could not find user {user_id}')
    net, target = floor(row[0]), floor(row[1]) if row[1] is not None else None

    # Current month total
    row = c.execute(
        'select total from stats_total where user_id = ? and category_id is null and year = ? and month = ?',
        (user_id, *period(today))
    ).fetchone()
    current_month = floor(row[0]) if row is not None else 0

    # Category totals
    rows = c.execute(
        'select c.name, total from stats_total left join categories c on category_id = c.id where user_id = ? and category_id is not null and year = ? and month = ?',
        (user_id, *period(today))
    )
    category_stats = {row[0]: floor(row[1]) for row in rows}

    return current_month, target, net, sorted(category_stats.items(), key=lambda x: -x[1])


def _avg_this_day(c: 'db.Cursor', user_id: int, category_id: Optional[int], now: datetime):
    row = c.execute('select timestamp from receipts order by timestamp asc limit 1').fetchone()
    if row is None:
        return 0
    epoch = datetime.fromtimestamp(row[0])

    tots = {
        row[0]: row[1]
        for row in c.execute(
            'select day, total from stats_days where user_id = ? and (category_id is not distinct from ?) and day <= ? order by day',
            (user_id, category_id, now.day)
        )
    }
    denoms = date_occurrences(epoch.date(), now.date())
    return floor(sum(tots[k]/denoms[k] for k in tots.keys()))


def category_table(user_id: int) -> (list[str], list[tuple[str, Decimal, list[Decimal]]]):
    c = db.cursor()
    categories = list(c.execute('select id, name from categories order by id'))
    rows = c.execute(
        'select year, month, category_id, total from stats_total where user_id = ? order by year desc, month desc, category_id nulls first',
        (user_id,))
    table = [
        (f'{year}.{month}', next(totals)[3],
            list(dense(map(lambda x: (x[2], x[3]), totals), Decimal('0'), start=1, stop=len(categories)+1)))
        for (year, month), totals in groupby(rows, lambda x: x[:2])
    ]
    return categories, table


def category_transactions(user_ids: list[int], year: int, month: int, category_id: int):
    c = db.cursor()
    user_rows = list(c.execute('select id from users order by id'))
    user_positions = {user_id: position for position, (user_id,) in enumerate(user_rows, start=1)}
    requested_positions = [user_positions[user_id] for user_id in user_ids if user_id in user_positions]
    if not requested_positions:
        return []

    end = app.config['PERIOD_END']
    if end == 0:
        start = datetime(year, month, 1)
        finish = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1)
    else:
        finish = datetime(year, month, end) + timedelta(days=1)
        previous_month = finish.replace(day=1) - timedelta(days=1)
        start = previous_month.replace(day=end + 1)

    rows = c.execute(
        'select r.id, r.timestamp, r.comment, ri.item_id, i.name, ri.quantity, ri.price, i.ean, i.splits '
        'from receipts r join receipts_items ri on ri.receipt_id = r.id '
        'join items i on i.id = ri.item_id '
        'where r.timestamp >= ? and r.timestamp < ? and i.category_id = ? '
        'order by r.timestamp desc, r.id desc, ri.sort',
        (start.timestamp(), finish.timestamp(), category_id))

    transactions = []
    for receipt_id, timestamp, comment, item_id, name, quantity, price, ean, splits in rows:
        item = Item.from_data(item_id, name, quantity, price, ean, splits, category_id)
        user_total = sum((item.split_total(position, count=len(user_rows)) for position in requested_positions), Decimal(0))
        transactions.append((receipt_id, datetime.fromtimestamp(timestamp), comment, item, user_total))
    return transactions


def monthly_user_totals(user_ids: list[int], year: int, month: int):
    c = db.cursor()
    if not user_ids:
        return []
    placeholders = ','.join('?' for _ in user_ids)
    users_rows = list(c.execute(
        f'select id, name from users where id in ({placeholders}) order by id', user_ids))
    totals = dict(c.execute(
        f'select user_id, total from stats_total where category_id is null and year = ? and month = ? '
        f'and user_id in ({placeholders})', [year, month, *user_ids]))
    return [(name, totals.get(user_id, Decimal('0'))) for user_id, name in users_rows]
