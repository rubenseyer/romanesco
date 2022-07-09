import os
import datetime

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import apsw

from .util import round_even

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

app.config.update(
    DATABASE_PATH=os.environ.get('DATABASE_PATH', './romanesco.db'),
    SECRET_KEY=os.environ.get('SECRET_KEY', 'secret'),
)

db = apsw.Connection(app.config['DATABASE_PATH'])

app.jinja_env.globals['now'] = datetime.datetime.now
app.jinja_env.globals['round'] = round_even

from . import login
from . import views
