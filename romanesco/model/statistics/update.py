from datetime import datetime
from decimal import Decimal
from typing import Optional

from .. import db
from ..receipt import Receipt


def stats_full_recompute():
    with db:
        c = db.cursor()

        # Reset all statistics
        c.execute('delete from stats_total; delete from stats_days; update users set net = \'0\';')

        # Recompute all
        for user_id, amount_str in c.execute('select user_id, amount from deposits order by rowid'):
            stats_new_deposit(user_id, Decimal(amount_str))
        for rid in c.execute('select id from receipts order by rowid'):
            r = Receipt.get(rid[0])
            r.save(update_items=False)
            stats_new_receipt(r)


def stats_new_deposit(user_id: int, amount: Decimal):
    with db:
        c = db.cursor()
        _inc_net(c, user_id, amount)


def stats_new_receipt(r: Receipt):
    totals = __extract_totals(r)
    with db:
        c = db.cursor()
        for i in range(1, len(totals[None])):
            # note negative: decrement net for receipt
            _inc_net(c, i, -totals[None][i])
            for category, total in totals.items():
                _inc_total(c, i, category, r.timestamp, total[i])
                _inc_avg(c, i, category, r.timestamp, total[i])


def stats_delete_receipt(r: Receipt):
    totals = __extract_totals(r)
    with db:
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
    net = Decimal(row[0])
    net += amount
    c.execute('update users set net = ? where id = ?', (str(net), user_id))


def _inc_total(c: 'db.Cursor', user_id: int, category_id: Optional[int], ts: datetime, amount: Decimal):
    row = c.execute('select total from stats_total where user_id = ? and category_id is ? and year = ? and month = ?',
                    (user_id, category_id, ts.year, ts.month)).fetchone()
    if row is None:
        c.execute('insert into stats_total (total, user_id, category_id, year, month) values (?,?,?,?,?)',
                  (str(amount), user_id, category_id, ts.year, ts.month))
    else:
        c.execute('update stats_total set total = ? where user_id = ? and category_id is ? and year = ? and month = ?',
                  (str(Decimal(row[0]) + amount), user_id, category_id, ts.year, ts.month))


def _inc_avg(c: 'db.Cursor', user_id: int, category_id: Optional[int], ts: datetime, amount: Decimal):
    row = c.execute('select total from stats_days where user_id = ? and category_id is ? and day = ?',
                    (user_id, category_id, ts.day)).fetchone()
    if row is None:
        c.execute('insert into stats_days (total, user_id, category_id, day) values (?,?,?,?)',
                  (str(amount), user_id, category_id, ts.day))
    else:
        c.execute('update stats_days set total = ? where user_id = ? and category_id is ? and day = ?',
                  (str(Decimal(row[0]) + amount), user_id, category_id, ts.day))
