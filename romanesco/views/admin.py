from flask import session, abort, redirect, url_for
from ..model.statistics import stats_full_recompute
from .. import app


@app.route('/debug_stats_recompute')
def debug_stats_recompute():
    if 'user_id' not in session:
        return abort(401)
    stats_full_recompute()
    return redirect(url_for('overview'))
