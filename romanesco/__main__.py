import sys
import os
from . import app


def main():
    host = os.environ.get('HOST', 'localhost')
    port = int(os.environ.get('PORT', 3000))
    use_reloader = bool(os.environ.get('USE_RELOADER', False))

    if use_reloader:
        # use dev server
        use_bjoern = False
    else:
        # try to use bjoern if it is installed
        try:
            import bjoern
            use_bjoern = True
        except ImportError:
            use_bjoern = False

    if '--single' in sys.argv[1:]:
        app.config['SINGLE_USER_MODE'] = True

    if use_bjoern:
        from logging import Formatter
        from flask.logging import default_handler
        print(f'Romanesco @ {host}:{port}')
        app.logger.setLevel('INFO')
        default_handler.setFormatter(Formatter(fmt='%(message)s'))
        try:
            bjoern.run(app, host, port, reuse_port=True)
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
    else:
        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=use_reloader
        )


if __name__ == '__main__':
    main()
