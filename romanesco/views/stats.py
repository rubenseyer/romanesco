from flask import g, redirect, url_for, render_template, abort, request
from ..model import users
from ..model.statistics import stats_full_recompute, category_table, monthly_user_totals, category_transactions
from .. import app
from .util import selected_user_ids


@app.route('/debug/stats_recompute')
def debug_stats_recompute():
    stats_full_recompute()
    return redirect(url_for('overview'))


@app.route('/stats')
def stats():
    all_users = users()
    all_user_ids = selected_user_ids(all_users)
    cats, table = category_table(all_user_ids[0])
    totals_by_period = {header: (total, values) for header, total, values in table}
    for user_id in all_user_ids[1:]:
        _, table_new = category_table(user_id)
        for header, total, values in table_new:
            previous_total, previous_values = totals_by_period.get(header, (0, [0] * len(cats)))
            totals_by_period[header] = (
                previous_total + total,
                [previous + value for previous, value in zip(previous_values, values)])
    table = [
        (header, *totals_by_period[header])
        for header in sorted(totals_by_period, key=lambda value: tuple(map(int, value.split('.'))), reverse=True)
    ]
    return render_template('stats.html', categories=cats, statistics=table,
                           users=all_users, selected_user_ids=all_user_ids,
                           query_user_id=','.join(str(user_id) for user_id in all_user_ids))


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
