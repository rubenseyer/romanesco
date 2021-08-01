import os
from flask import Flask
import apsw
import datetime
from .util import round_even

app = Flask(__name__)

app.config.update(
    DATABASE_PATH=os.environ['DATABASE_PATH'],
    SECRET_KEY=os.environ['SECRET_KEY'],
)

db = apsw.Connection(app.config['DATABASE_PATH'])

app.jinja_env.globals['now'] = datetime.datetime.now
app.jinja_env.globals['round'] = round_even

#from . import filters
from . import views
