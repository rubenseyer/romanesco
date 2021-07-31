from flask import request, render_template, session, redirect, url_for, abort
from ..model import users, stats_overview, events
from ..util import round
from .. import app


@app.route('/')
def overview():
    if 'user_id' not in session:
        return redirect(url_for('login'), 307)
    current_month, avg_this_day, net, category_stats = stats_overview(session['user_id'])
    # TODO
    return render_template('index.html', current_month=current_month, avg_this_day=avg_this_day, net=net, category_stats=category_stats)


@app.route('/events/')
def events_fetch():
    if 'user_id' not in session:
        return abort(401)
    page = request.args.get('page', 0, type=int)
    return render_template('_events.html', events=events(session['user_id'], page=page), round=round)


@app.route('/login')
@app.route('/login/<int:user_id>')
def login(user_id=None):
    users_dict = users()
    basic_auth_name = request.headers.get('X-Remote-User')
    if basic_auth_name is not None:
        for id, name in users_dict.items():
            if name.lower() == basic_auth_name:
                user_id = id
                break
    if user_id is None:
        return render_template('login.html', users=users_dict)
    if user_id not in users_dict:
        abort(404)
    session['user_id'] = user_id
    session['user_name'] = users_dict[user_id]
    session.permanent = True
    return redirect(url_for('overview'))
