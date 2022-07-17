import os
import datetime
from importlib.resources import files

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import apsw

from .logger import LoggerMiddleware
from .util import round_even

app = Flask(__name__)
app.wsgi_app = LoggerMiddleware(app.wsgi_app, app.logger)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config.update(
    DATABASE_PATH=os.environ.get('DATABASE_PATH', './romanesco.db'),
    SECRET_KEY=os.environ.get('SECRET_KEY', 'secretsecretsecretsecretsecretsecretsecretx='),
)

db = apsw.Connection(app.config['DATABASE_PATH'])
with db:
    db.cursor().execute(files('romanesco').joinpath('schema.sql').read_text())

app.jinja_env.globals['now'] = datetime.datetime.now
app.jinja_env.globals['round'] = round_even

from . import login
from . import views
