from .. import db


def templates():
    c = db.cursor()
    return {id: name for id, name in c.execute(
        'select receipt_id, comment from templates_receipts left join receipts on receipt_id = id')}


def new_template(id: int):
    c = db.cursor()
    c.execute('insert into templates_receipts (receipt_id) values (?)', (id,))


def delete_template(id: int):
    c = db.cursor()
    c.execute('delete from templates_receipts where receipt_id = ?', (id,))
