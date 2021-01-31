from decimal import Decimal
from datetime import datetime
from flask import render_template, request, redirect, url_for
from ..model import users, stats_new_deposit
from .. import app, db


@app.route('/deposit', methods=['GET', 'POST'])
def deposit_new():
    users_dict = users()
    if request.method == 'GET':
        return render_template('deposit_new.html', users=users_dict)

    if 'user_id' not in request.form or int(request.form['user_id']) not in users_dict:
        return render_template('deposit_new.html', error='Fel: icke-existerande användare')
    user_id = int(request.form['user_id'])
    try:
        timestamp = datetime.fromisoformat(request.form['timestamp'])
    except KeyError:
        return render_template('deposit_new.html', error='Fel: datum saknas')
    except ValueError:
        return render_template('deposit_new.html', error='Fel: felaktigt datum')
    try:
        amount = Decimal(request.form['amount'])
    except KeyError:
        return render_template('deposit_new.html', error='Fel: summa saknas')
    except ValueError:
        return render_template('deposit_new.html', error='Fel: felaktig summa')

    # yeah model in view but don't need a module for 3 lines
    c = db.cursor()
    c.execute('insert into deposits (user_id, timestamp, amount, comment) values (?,?,?,?)',
              (user_id, timestamp.timestamp(), str(amount), request.form.get('comment', '')))
    stats_new_deposit(user_id, amount)

    return redirect(url_for('overview'))
