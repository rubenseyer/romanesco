import os
from . import app

# Running romanesco directly enables single user mode
app.config['SINGLE_USER_MODE'] = True

app.run(
    host=os.environ.get('HOST', 'localhost'),
    port=int(os.environ.get('PORT', 3000)),
    debug=True,
    use_reloader=bool(os.environ.get('USE_RELOADER', False))
)
