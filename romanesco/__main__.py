import os
from . import app

app.run(
    host=os.environ.get('HOST', 'localhost'),
    port=int(os.environ.get('PORT', 3000)),
    debug=True,
    use_reloader=bool(os.environ.get('USE_RELOADER', False))
)
