from datetime import datetime
from decimal import Decimal
from .. import db


def deposit_history(user_ids: list[int]):
    if not user_ids:
        return []
    placeholders = ','.join('?' for _ in user_ids)
    rows = db.cursor().execute(
        'select d.timestamp, u.name, d.amount, d.comment '
        'from deposits d join users u on u.id = d.user_id '
        f'where d.user_id in ({placeholders}) '
        'order by d.timestamp desc, u.id', user_ids)
    return [(datetime.fromtimestamp(timestamp), name, amount, comment)
            for timestamp, name, amount, comment in rows]


def new_deposit(user_id: int, timestamp: datetime, amount: Decimal, comment: str):
    c = db.cursor()
    c.execute('insert into deposits (user_id, timestamp, amount, comment) values (?,?,?,?)',
              (user_id, timestamp.timestamp(), amount, comment))
