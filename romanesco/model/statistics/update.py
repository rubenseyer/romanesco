from datetime import datetime
from decimal import Decimal
from typing import Optional
from time import perf_counter_ns

from ... import app, db
from ..receipt import Receipt


def stats_full_recompute():
    app.logger.info('Starting full stats recompute')
    with db.transaction():
        c = db.cursor()

        # Reset all statistics (apsw could have combined the queries)
        tic = perf_counter_ns()
        c.execute('delete from stats_total')
        c.execute('delete from stats_days')
        c.execute('update users set net = ?', (Decimal('0'),))
        app.logger.info(f'Cleared data in {(perf_counter_ns() - tic)*1e-6} ms')

        # Recompute all
        tic = perf_counter_ns()
        for user_id, amount in c.execute('select user_id, amount from deposits order by timestamp'):
            stats_new_deposit(user_id, amount)
        app.logger.info(f'Deposits added in {(perf_counter_ns() - tic) * 1e-6} ms')
        tic = perf_counter_ns()
        for rid in c.execute('select id from receipts order by id'):
            r = Receipt.get(rid[0])
            r.save(update_items=False)
            stats_new_receipt(r)
        app.logger.info(f'Receipts added in {(perf_counter_ns() - tic) * 1e-9} s')
    app.logger.info('Completed full stats recompute')


def stats_new_deposit(user_id: int, amount: Decimal):
    with db.transaction():
        c = db.cursor()
        _inc_net(c, user_id, amount)


def stats_new_receipt(r: Receipt):
    totals = __extract_totals(r)
    with db.transaction():
        c = db.cursor()
        for i in range(1, len(totals[None])):
            # note negative: decrement net for receipt
            _inc_net(c, i, -totals[None][i])
            for category, total in totals.items():
                _inc_total(c, i, category, r.timestamp, total[i])
                _inc_avg(c, i, category, r.timestamp, total[i])


def stats_delete_receipt(r: Receipt):
    totals = __extract_totals(r)
    with db.transaction():
        c = db.cursor()
        for i in range(1, len(totals[None])):
            # note positive: return net for removed receipt
            _inc_net(c, i, +totals[None][i])
            for category, total in totals.items():
                _inc_total(c, i, category, r.timestamp, -total[i])
                _inc_avg(c, i, category, r.timestamp, -total[i])


def stats_update_receipt(r_old: Receipt, r_new: Receipt):
    stats_delete_receipt(r_old)
    stats_new_receipt(r_new)


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
    net = row[0] + amount
    c.execute('update users set net = ? where id = ?', (net, user_id))


def _inc_total(c: 'db.Cursor', user_id: int, category_id: Optional[int], ts: datetime, amount: Decimal):
    row = c.execute('select total from stats_total where user_id = ? and (category_id is not distinct from ?) and year = ? and month = ?',
                    (user_id, category_id, *period(ts))).fetchone()
    if row is None:
        c.execute('insert into stats_total (total, user_id, category_id, year, month) values (?,?,?,?,?)',
                  (amount, user_id, category_id, *period(ts)))
    else:
        c.execute('update stats_total set total = ? where user_id = ? and (category_id is not distinct from ?) and year = ? and month = ?',
                  ((row[0] + amount), user_id, category_id, *period(ts)))


def _inc_avg(c: 'db.Cursor', user_id: int, category_id: Optional[int], ts: datetime, amount: Decimal):
    row = c.execute('select total from stats_days where user_id = ? and (category_id is not distinct from ?) and day = ?',
                    (user_id, category_id, ts.day)).fetchone()
    if row is None:
        c.execute('insert into stats_days (total, user_id, category_id, day) values (?,?,?,?)',
                  (amount, user_id, category_id, ts.day))
    else:
        c.execute('update stats_days set total = ? where user_id = ? and (category_id is not distinct from ?) and day = ?',
                  ((row[0] + amount), user_id, category_id, ts.day))


def period(ts: datetime, end=app.config['PERIOD_END']) -> (int, int):
    # If PERIOD_END is set to zero, we use the calendar as is.
    # This was the previous default.
    if end == 0:
        return ts.year, ts.month
    # Otherwise, the current month contains everything up to and including
    # the end date, and anything after that gets pushed forward.
    # This would then work like a credit card.
    year, month = ts.year, ts.month
    if ts.day > end:
        month += 1
    if month == 13:
        year += 1
        month = 1
    return year, month


def target_set(user_id: int, target: Decimal):
    with db.transaction():
        c = db.cursor()
        c.execute('update users set target = ? where id = ?', (target, user_id))