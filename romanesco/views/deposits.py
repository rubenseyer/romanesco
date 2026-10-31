from decimal import Decimal, InvalidOperation
from datetime import datetime
from flask import render_template, request, redirect, url_for
from ..model import users, new_deposit, stats_new_deposit
from ..model.deposits import deposit_history
from .. import app, db
from .util import selected_user_ids


@app.route('/deposit', methods=['GET', 'POST'])
def deposits():
    all_users = users()
    user_ids = selected_user_ids(all_users)

    error = None
    if request.method == 'POST':
        try:
            user_id = int(request.form.get('user_id', ''))
            if user_id not in all_users:
                raise ValueError
        except ValueError:
            error = 'Fel: icke-existerande användare'
        if error is None:
            try:
                timestamp = datetime.fromisoformat(request.form['timestamp'])
            except KeyError:
                error = 'Fel: datum saknas'
            except ValueError:
                error = 'Fel: felaktigt datum'
        if error is None:
            try:
                amount = Decimal(request.form['amount'])
                if not amount.is_finite():
                    raise InvalidOperation
            except KeyError:
                error = 'Fel: summa saknas'
            except InvalidOperation:
                error = 'Fel: felaktig summa'
        if error is None:
            with db.transaction():
                new_deposit(user_id, timestamp, amount, request.form.get('comment', ''))
                stats_new_deposit(user_id, amount)
            return redirect(url_for('deposits', id=user_ids), code=303)

    history = deposit_history(user_ids)
    return render_template('deposits.html', deposits=history, users=all_users,
                           selected_user_ids=user_ids, error=error,
                           total=sum((row[2] for row in history), Decimal('0')))
