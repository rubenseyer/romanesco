from flask import session, abort, redirect, url_for, render_template
from ..model.statistics import stats_full_recompute, stats_category_table, stats_user_table
from .. import app


@app.route('/debug/stats_recompute')
def debug_stats_recompute():
    if 'user_id' not in session:
        return abort(401)
    stats_full_recompute()
    return redirect(url_for('overview'))


@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return abort(401)
    cats, table = stats_category_table(session['user_id'])
    return render_template('stats_category_totals.html', categories=cats, statistics=table)


@app.route('/stats/statement')
def stats_statement():
    if 'user_id' not in session:
        return abort(401)
    users, table = stats_user_table()
    return render_template('stats_user_totals.html', users=users, statistics=table)
