from datetime import datetime
from decimal import Decimal
from math import floor
from typing import Optional
from itertools import groupby

from ...util import dense
from .update import period
from .util_dateocc import date_occurrences

from .. import db


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


def stats_category_table(user_id: int) -> (list[str], list[tuple[str, Decimal, list[Decimal]]]):
    c = db.cursor()
    categories = [x[0] for x in c.execute('select name from categories order by id')]
    rows = c.execute(
        'select year, month, category_id, total from stats_total where user_id = ? order by year desc, month desc, category_id nulls first',
        (user_id,))
    table = [
        (f'{year}.{month}', next(totals)[3],
            list(dense(map(lambda x: (x[2], x[3]), totals), Decimal('0'), start=1, stop=len(categories)+1)))
        for (year, month), totals in groupby(rows, lambda x: x[:2])
    ]
    return categories, table


def stats_user_table() -> (list[str], list[tuple[str, list[Decimal]]]):
    c = db.cursor()
    users_rows = list(c.execute('select name, net, target from users order by id'))
    rows = c.execute('select year, month, user_id, total from stats_total where category_id is null order by year desc, month desc, user_id asc')
    table = [
        (f'{year}.{month}',
            list(dense(map(lambda x: (x[2], x[3]), totals), Decimal('0'), start=1, stop=len(users_rows) + 1)))
        for (year, month), totals in groupby(rows, lambda x: x[:2])
    ]
    users, nets, targets = list(zip(*users_rows))
    table.insert(0, ('-', nets))
    return users, table, targets
