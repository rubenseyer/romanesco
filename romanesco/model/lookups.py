from datetime import datetime
from decimal import Decimal
from .. import db


def users():
    c = db.cursor()
    return {id: name for id, name in c.execute('select id, name from users order by id')}


def categories():
    c = db.cursor()
    return {id: name for id, name in c.execute('select id, name from categories order by id')}


def events(user_id, page=0, limit=30):
    c = db.cursor()
    rows = c.execute(
        'select id, timestamp, comment, cached_totals, automatic from receipts union all \
         select NULL, timestamp, comment, cast(amount as text), false from deposits where deposits.user_id = ? \
         order by timestamp desc limit ? offset ?',
        (user_id, limit, page * limit))
    return [
        (id, datetime.fromtimestamp(ts), c, [Decimal(s) for s in am.split(',')], auto) if id is not None else
        (None, datetime.fromtimestamp(ts), c, Decimal(am), auto) for id, ts, c, am, auto in rows]
