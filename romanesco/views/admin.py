from flask import session, abort, redirect, url_for, render_template
from ..model.statistics import stats_full_recompute, stats_all_category_stats
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
    return render_template('stats_totals.html', statistics=stats_all_category_stats(session['user_id']))

