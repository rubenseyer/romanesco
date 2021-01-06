from flask import Flask
from supersqlite import SuperSQLite

app = Flask(__name__)

# TODO config by env?
app.config['DATABASE_PATH'] = '/home/ruben/Development/romanesco/test/romanesco.db'

db = SuperSQLite.connect(app.config['DATABASE_PATH'])


#from . import filters
from . import views


if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True)
