from flask import request, render_template, g
from ..model import stats_overview, events
from .. import app


@app.route('/')
def overview():
    current_month, avg_this_day, net, category_stats = stats_overview(g.user_id)
    # TODO
    return render_template('index.html', current_month=current_month, avg_this_day=avg_this_day, net=net, category_stats=category_stats)


@app.route('/events/')
def events_fetch():
    page = request.args.get('page', 0, type=int)
    return render_template('_events.html', events=events(g.user_id, page=page))

