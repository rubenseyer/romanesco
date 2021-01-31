from datetime import datetime
from decimal import Decimal
from .. import db


def users():
    c = db.cursor()
    return {id: name for id, name in c.execute('select id, name from users order by rowid')}


def categories():
    c = db.cursor()
    return {id: name for id, name in c.execute('select id, name from categories order by rowid')}


def events(user_id, page=0, limit=30):
    c = db.cursor()
    rows = c.execute(
        'select id, timestamp, comment, cached_totals from receipts union all \
         select NULL, timestamp, comment, amount from deposits where deposits.user_id = ? \
         order by timestamp desc limit ? offset ?',
        (user_id, limit, page * limit))
    return [
        (id, datetime.fromtimestamp(ts), c, [Decimal(s) for s in am.split(',')]) if id is not None else
        (None, datetime.fromtimestamp(ts), c, Decimal(am)) for id, ts, c, am in rows]
