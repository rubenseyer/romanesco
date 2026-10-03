from decimal import Decimal
from flask import g, redirect, url_for, render_template, abort, request
from ..model import users
from ..model.statistics import stats_full_recompute, stats_overview, category_table, monthly_user_totals, target_set, category_transactions
from .. import app


@app.route('/debug/stats_recompute')
def debug_stats_recompute():
    stats_full_recompute()
    return redirect(url_for('overview'))


@app.route('/stats')
def stats():
    all_users = users()
    query_user_id = request.args.getlist('id')
    try:
        all_user_ids = [int(user_id) for value in query_user_id for user_id in value.split(',')] or [g.user_id]
    except ValueError:
        abort(400)
    if not all_user_ids or any(user_id not in all_users for user_id in all_user_ids):
        abort(400)
    cats, table = category_table(all_user_ids[0])
    for user_id in all_user_ids[1:]:
        _, table_new = category_table(user_id)
        table = [
            (header, sum1+sum2, [c1+c2 for c1, c2 in zip(cols1, cols2)])
            for (header, sum1, cols1), (_, sum2, cols2) in zip(table, table_new)
        ]
    return render_template('stats.html', categories=cats, statistics=table,
                           users=all_users, selected_user_ids=all_user_ids,
                           query_user_id=','.join(str(user_id) for user_id in all_user_ids),
                           target=stats_overview(g.user_id)[1])


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


@app.route('/stats/user-totals')
def stats_user_totals():
    try:
        year = int(request.args['year'])
        month = int(request.args['month'])
        user_ids = [int(x) for x in request.args['id'].split(',')]
    except (KeyError, TypeError, ValueError):
        abort(400)
    if not 1 <= month <= 12:
        abort(400)
    totals = monthly_user_totals(user_ids, year, month)
    return render_template('stats_user_totals.html', totals=totals)


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
