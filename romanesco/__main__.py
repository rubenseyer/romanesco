import sys
import os
from . import app, db


def main():
    host = os.environ.get('HOST', 'localhost')
    port = int(os.environ.get('PORT', 3000))
    use_reloader = bool(os.environ.get('USE_RELOADER', False))

    if '--single' in sys.argv[1:]:
        app.config['SINGLE_USER_MODE'] = True

    if not use_reloader:
        from logging import Formatter
        from flask.logging import default_handler
        from gunicorn.app.base import BaseApplication

        class RomanescoApplication(BaseApplication):
            def __init__(self, application, options=None):
                self.options = options or {}
                self.application = application
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        app.logger.info(f'Romanesco @ {host}:{port}')
        app.logger.setLevel('INFO')
        default_handler.setFormatter(Formatter(fmt='%(message)s'))
        try:
            RomanescoApplication(
                app,
                {'bind': f'{host}:{port}', 'reuse_port': True},
            ).run()
        except KeyboardInterrupt:
            app.logger.warning('Interrupted')
            db.close()
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
