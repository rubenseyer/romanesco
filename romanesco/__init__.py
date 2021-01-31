from flask import Flask
from supersqlite import SuperSQLite, SuperSQLiteConnection
import datetime

app = Flask(__name__)

# TODO config by env?
app.config['DATABASE_PATH'] = '/home/ruben/Development/romanesco/test/romanesco.db'
app.config['SECRET_KEY'] = 'CHANGEME'

db: SuperSQLiteConnection = SuperSQLite.connect(app.config['DATABASE_PATH'])

app.jinja_env.globals['now'] = datetime.datetime.now

#from . import filters
from . import views
