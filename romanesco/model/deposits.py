from datetime import datetime
from decimal import Decimal
from .. import db


def new_deposit(user_id: int, timestamp: datetime, amount: Decimal, comment: str):
    c = db.cursor()
    c.execute('insert into deposits (user_id, timestamp, amount, comment) values (?,?,?,?)',
              (user_id, timestamp.timestamp(), amount, comment))
