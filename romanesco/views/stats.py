from decimal import Decimal
from flask import g, redirect, url_for, render_template, abort, request
from ..model.statistics import stats_full_recompute, category_table, user_table, target_set, category_transactions
from .. import app


@app.route('/debug/stats_recompute')
def debug_stats_recompute():
    stats_full_recompute()
    return redirect(url_for('overview'))


@app.route('/stats')
def stats():
    query_user_id = request.args.get('id')
    if query_user_id is None:
        cats, table = category_table(g.user_id)
    else:
        all_user_ids = [int(x) for x in query_user_id.split(',')]
        cats, table = category_table(all_user_ids[0])
        for user_id in all_user_ids[1:]:
            _, table_new = category_table(user_id)
            table = [
                (header, sum1+sum2, [c1+c2 for c1, c2 in zip(cols1, cols2)])
                for (header, sum1, cols1), (_, sum2, cols2) in zip(table, table_new)
            ]
    return render_template('stats_category_totals.html', categories=cats, statistics=table, query_user_id=query_user_id)


@app.route('/stats/category-transactions')
def stats_category_transactions():
    try:
        year = int(request.args['year'])
        month = int(request.args['month'])
        category_id = int(request.args['category_id'])
        user_ids = [int(x) for x in request.args.get('id', str(g.user_id)).split(',')]
    except (KeyError, TypeError, ValueError):
        abort(400)
    if not 1 <= month <= 12:
        abort(400)
    transactions = category_transactions(user_ids, year, month, category_id)
    return render_template('stats_category_transactions.html', transactions=transactions)


@app.route('/stats/statement')
def stats_statement():
    users, table, targets = user_table()
    return render_template('stats_user_totals.html', users=users, statistics=table, target=targets[g.user_id-1])


@app.route('/stats/budget', methods=['POST'])
def stats_budget():
    try:
        target = Decimal(request.form['target'])
    except KeyError:
        # missing from form
        abort(400)
    except ValueError:
        # parse error
        abort(400)

    target_set(g.user_id, target)

    return redirect(url_for('overview'), code=303)
