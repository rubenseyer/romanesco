import os
import datetime
from importlib.resources import files
import warnings

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .logger import LoggerMiddleware
from .util import round_even
from .xdb import connect_db

app = Flask(__name__)
app.wsgi_app = LoggerMiddleware(app.wsgi_app, app.logger)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

if 'DATABASE' not in os.environ:
    warnings.warn('No database configured... defaulting to local directory.')
if 'SECRET_KEY' not in os.environ:
    warnings.warn('No secret key configured... defaulting to dummy key.')

app.config.update(
    DATABASE=os.environ.get('DATABASE', 'sqlite://./romanesco.db'),
    SECRET_KEY=os.environ.get('SECRET_KEY', 'secretsecretsecretsecretsecretsecretsecretx='),
)

db = connect_db(app.config['DATABASE'])
with db.transaction():
    c = db.cursor()
    c.execute(files('romanesco').joinpath(f'xdb/schema_{db.type}.sql').read_text())

app.jinja_env.globals['now'] = datetime.datetime.now
app.jinja_env.globals['round'] = round_even

from . import login
from . import views
