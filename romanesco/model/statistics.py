from datetime import datetime
from decimal import Decimal
from math import floor
from typing import Optional

from .. import db
from ..model import users
from .receipt import Receipt


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
    row = c.execute(
        'select cum_avg from stats_avg where user_id = ? and category_id is null and day <= ? order by day desc limit 1',
        (user_id, today.day)).fetchone()
    avg_this_day = floor(Decimal(row[0])) if row is not None else 0

    # Category totals
    rows = c.execute(
        'select c.name, total from stats_total left join categories c on category_id = c.id where user_id = ? and category_id is not null and year = ? and month = ?',
        (user_id, today.year, today.month))
    category_stats = {row[0]: floor(Decimal(row[1])) for row in rows}

    return current_month, avg_this_day, net, sorted(category_stats.items(), key=lambda x: -x[1])


def stats_all_category_stats(user_id: int):
    c = db.cursor()
    category_stats = {}
    rows = c.execute(
        'select year, month, c.name, total from stats_total left join categories c on category_id = c.id where user_id = ? and category_id is not null',
        (user_id,))
    for year, month, name, rtotal in rows:
        cat = category_stats.setdefault(f'{year}.{month}', dict())
        cat[name] = floor(Decimal(rtotal))
    return category_stats


def stats_full_recompute():
    with db:
        c = db.cursor()

        # Reset all statistics
        c.execute('delete from stats_total; delete from stats_avg; update users set net = \'0\';')

        # Recompute all
        for user_id, amount_str in c.execute('select user_id, amount from deposits order by rowid'):
            stats_new_deposit(user_id, Decimal(amount_str))
        for rid in c.execute('select id from receipts order by rowid'):
            r = Receipt.get(rid[0])
            r.recalculate(cache=True)
            stats_new_receipt(r, future_blind=True)


def stats_new_deposit(user_id: int, amount: Decimal):
    with db:
        c = db.cursor()
        _inc_net(c, user_id, amount)


def stats_new_receipt(r: Receipt, future_blind=False):
    totals = __extract_totals(r)
    with db:
        c = db.cursor()
        for i in range(1, len(totals[None])):
            # note negative: decrement net for receipt
            _inc_net(c, i, -totals[None][i])
            for category, total in totals.items():
                _inc_total(c, i, category, r.timestamp.year, r.timestamp.month, total[i])
                _obs_avg(c, r.id, i, category, r.timestamp, total[i], future_blind=future_blind)


def stats_update_receipt(r_old: Receipt, r_new: Receipt):
    totals_old = __extract_totals(r_old)
    totals_new = __extract_totals(r_new)
    totals_delta = {}
    for category in {*totals_old.keys(), *totals_new.keys()}:
        if category not in totals_new:
            totals_delta[category] = [-x for x in totals_old[category]]
        elif category not in totals_old:
            totals_delta[category] = totals_new[category]
        else:
            totals_delta[category] = list(map(lambda z: z[0] - z[1], zip(totals_new[category], totals_old[category])))
    same_year = r_new.timestamp.year == r_old.timestamp.year
    same_month = r_new.timestamp.month == r_old.timestamp.month
    same_day = r_new.timestamp.day == r_old.timestamp.day
    with db:
        c = db.cursor()
        if same_year and same_month and same_day:
            for i in range(1, len(totals_delta[None])):
                # note negative: decrement net for receipt
                _inc_net(c, i, -totals_delta[None][i])
                for category, total in totals_delta.items():
                    _inc_total(c, i, category, r_new.timestamp.year, r_new.timestamp.month, total[i])
                    _obs_avg(c, r_new.id, i, category, r_new.timestamp, total[i], obs=0)
        elif same_year and same_month:
            for i in range(1, len(totals_delta[None])):
                # note negative: decrement net for receipt
                _inc_net(c, i, -totals_delta[None][i])
                for category, total in totals_delta.items():
                    _inc_total(c, i, category, r_new.timestamp.year, r_new.timestamp.month, total[i])
                    if category in totals_old:
                        _obs_avg(c, r_old.id, i, category, r_old.timestamp, -totals_old[category][i], obs=-1)
                    if category in totals_new:
                        _obs_avg(c, r_new.id, i, category, r_new.timestamp, totals_new[category][i], obs=1)
        else:
            for i in range(1, len(totals_delta[None])):
                # note negative: decrement net for receipt
                _inc_net(c, i, -totals_delta[None][i])
                for category, total in totals_delta.keys():
                    if category in totals_old:
                        _inc_total(c, i, category, r_old.timestamp.year, r_old.timestamp.month, -totals_old[category][i])
                        _obs_avg(c, r_old.id, i, category, r_old.timestamp, -totals_old[category][i], obs=-1)
                    if category in totals_new:
                        _inc_total(c, i, category, r_new.timestamp.year, r_new.timestamp.month, totals_new[category][i])
                        _obs_avg(c, r_new.id, i, category, r_new.timestamp, totals_new[category][i], obs=1)


def __extract_totals(r: Receipt):
    sz = len(r._totals)
    totals: dict[Optional[int], list[Decimal]] = {None: r._totals}
    for item in r.items:
        totals.setdefault(item.category, [Decimal(0)] * sz)
        totals[item.category][0] += item.total()
        for i in range(1, sz):
            totals[item.category][i] += item.split_total(i, count=sz - 1)
    return totals


def _inc_net(c: 'db.Cursor', user_id: int, amount: Decimal):
    row = c.execute('select net from users where id = ?', (user_id,)).fetchone()
    if row is None:
        raise LookupError(f'could not find user {user_id}')
    net = Decimal(row[0])
    net += amount
    c.execute('update users set net = ? where id = ?', (str(net), user_id))


def _inc_total(c: 'db.Cursor', user_id: int, category_id: int, year: int, month: int, amount: Decimal):
    row = c.execute('select total from stats_total where user_id = ? and category_id is ? and year = ? and month = ?',
                    (user_id, category_id, year, month)).fetchone()
    total = Decimal(row[0]) if row is not None else Decimal('0')
    total += amount
    if row is None:
        c.execute('insert into stats_total (total, user_id, category_id, year, month) values (?,?,?,?,?)',
                  (str(total), user_id, category_id, year, month))
    else:
        c.execute('update stats_total set total = ? where user_id = ? and category_id is ? and year = ? and month = ?',
                  (str(total), user_id, category_id, year, month))


def _obs_avg(c: 'db.Cursor', receipt_id: int, user_id: int, category_id: int, ts: datetime, amount: Decimal, obs: int = 1, future_blind = False):
    row = c.execute('select avg from stats_avg where user_id = ? and category_id is ? and day = ?',
                    (user_id, category_id, ts.day)).fetchone()
    avg = Decimal(row[0] if row is not None else '0')
    nobs = next(c.execute('select nobs from stats_avg where user_id = ? and category_id is null and day = ?',
                          (user_id, ts.day)), (0,))[0]
    cum_avg = Decimal(next(c.execute('select cum_avg from stats_avg where user_id = ? and category_id is ? and day < ? order by day desc limit 1',
                                     (user_id, category_id, ts.day)), (0,))[0] if ts.day > 1 else '0')
    if not future_blind:
        count_others = c.execute('select count(rowid) from receipts where id != ? and date(timestamp,\'unixepoch\') == ?',
                                 (receipt_id, ts.date().isoformat())).fetchone()[0]
    else:
        count_others = c.execute('select count(rowid) from receipts where id < ? and date(timestamp,\'unixepoch\') == ?',
                                 (receipt_id, ts.date().isoformat())).fetchone()[0]
    if count_others == 0:
        avg = (nobs*avg + amount)/(nobs + obs)
        nobs += obs
    else:
        avg = (nobs * avg + amount) / nobs
    cum_avg += avg
    if row is None:
        c.execute('insert into stats_avg (cum_avg, avg, user_id, category_id, day) values (?,?,?,?,?)',
                  (str(cum_avg), str(avg), user_id, category_id, ts.day))
    else:
        c.execute('update stats_avg set cum_avg = ?, avg = ? where user_id = ? and category_id is ? and day = ?',
                  (str(cum_avg), str(avg), user_id, category_id, ts.day))
    if category_id is None:
        c.execute('update stats_avg set nobs = ? where user_id = ? and category_id is null and day = ?',
                  (nobs, user_id, ts.day))

    future_avg_rows = c.execute('select day, avg from stats_avg where user_id = ? and category_id is ? and day > ? order by day',
                                 (user_id, category_id, ts.day))
    for row in list(future_avg_rows):
        cum_avg += Decimal(row[1])
        c.execute('update stats_avg set cum_avg = ? where user_id = ? and category_id is ? and day = ?',
                  (str(cum_avg), user_id, category_id, row[0]))
