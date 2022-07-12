from flask import request, g, session, abort
from decimal import Decimal
from . import app, db


@app.before_request
def before_request():
    if 'user_id' in session:
        g.user_id = session['user_id']
        g.user_name = session['user_name']
        return

    c = db.cursor()
    if not app.config.get('SINGLE_USER_MODE', False):
        user_name = request.headers.get('X-Remote-User')
        if user_name is None:
            abort(401)
        user_name = user_name.title()
        row = c.execute('select id from users where name = ?', (user_name,)).fetchone()
        if row is not None:
            user_id = row[0]
        else:
            c.execute('insert into users (id, name, net) values (null,?,?)', (user_name, '0'))
            user_id = db.last_insert_rowid()
    else:  # Single user mode
        user_id = 1
        row = c.execute('select name from users where id = ?', (user_id,)).fetchone()
        if row is not None:
            user_name = row[0]
        else:
            user_name = 'User'
            c.execute('insert into users (id, name, net) values (?,?,?)', (user_id, user_name, '0'))

    g.user_id = session['user_id'] = user_id
    g.user_name = session['user_name'] = user_name
