import os
from flask import Flask
from supersqlite import SuperSQLite, SuperSQLiteConnection
import datetime
from .util import round

app = Flask(__name__)

app.config.update(
    DATABASE_PATH = os.environ['DATABASE_PATH'],
    SECRET_KEY = os.environ['SECRET_KEY'],
)

db: SuperSQLiteConnection = SuperSQLite.connect(app.config['DATABASE_PATH'])

app.jinja_env.globals['now'] = datetime.datetime.now
app.jinja_env.globals['round'] = round

#from . import filters
from . import views
