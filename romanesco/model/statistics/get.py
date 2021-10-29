from datetime import datetime
from decimal import Decimal
from math import floor
from typing import Optional

from .util_dateocc import date_occurrences

from .. import db


def stats_overview(user_id: int):
    c = db.cursor()
    today = datetime.today()

    # Net
    row = c.execute('select net from users where id = ?', (user_id,)).fetchone()
    if row is None:
        raise LookupError(f'could not find user {user_id}')
    net = floor(Decimal(row[0]))

    # Current month total
    row = c.execute(
        'select total from stats_total where user_id = ? and category_id is null and year = ? and month = ?',
        (user_id, today.year, today.month)).fetchone()
    current_month = floor(Decimal(row[0])) if row is not None else 0

    # Current day in month avg
    avg_this_day = _avg_this_day(c, user_id, None, today)

    # Category totals
    rows = c.execute(
        'select c.name, total from stats_total left join categories c on category_id = c.id where user_id = ? and category_id is not null and year = ? and month = ?',
        (user_id, today.year, today.month))
    category_stats = {row[0]: floor(Decimal(row[1])) for row in rows}

    return current_month, avg_this_day, net, sorted(category_stats.items(), key=lambda x: -x[1])


def _avg_this_day(c: 'db.Cursor', user_id: int, category_id: Optional[int], now: datetime):
    row = c.execute('select timestamp from receipts order by timestamp asc limit 1').fetchone()
    if row is None:
        return 0
    epoch = datetime.fromtimestamp(row[0])

    tots = {row[0]: Decimal(row[1]) for row in c.execute('select day, total from stats_days where user_id = ? and category_id is ? and day <= ? order by day', (user_id, category_id, now.day))}
    denoms = date_occurrences(epoch.date(), now.date())
    return floor(sum(tots[k]/denoms[k] for k in tots.keys()))


def stats_all_category_stats(user_id: int):
    c = db.cursor()
    category_stats = {}
    rows = c.execute(
        'select year, month, c.name, total from stats_total left join categories c on category_id = c.id where user_id = ? and category_id is not null',
        (user_id,))
    for year, month, name, rtotal in rows:
        cat = category_stats.setdefault((year, month), dict())
        cat[name] = Decimal(rtotal)
    return category_stats


def stats_all_totals():
    c = db.cursor()
    total_stats = {}
    rows = c.execute('select year, month, total from stats_total where category_id is null')
    for year, month, rtotal in rows:
        total_stats[(year, month)] = total_stats.get((year, month), 0) + Decimal(rtotal)
    return total_stats
