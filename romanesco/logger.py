import logging
import time

NOCLR_STR = '{method} {host}/{request'
COLOR_STR = NOCLR_STR #''

class LoggerMiddleware():
    def __init__(self, wsgi_app, logger, *, color=True):
        self.wsgi_app = wsgi_app
        self.logger = logger

    def format(self, environ, status, length, elapsed):
        method = environ['REQUEST_METHOD']
        status = status[:3]
        req = environ.get('PATH_INFO', '')
        req += '?' if environ.get('QUERY_STRING', '') else ''
        req += environ.get('QUERY_STRING', '')
        proto = environ.get('SERVER_PROTOCOL', '')
        remoteaddr = environ['REMOTE_ADDR']
        length = f'{length/1e3:.3f}kB ' if length is not None else ''
        return f'{method} {req} {proto} from {remoteaddr} - {status} {length}{elapsed:.2f}ms'

    def __call__(self, environ, start_response):
        start_time = time.perf_counter()
        status_code_out = None
        content_length = None
        def wrapped_start_response(status_code, response_headers, exc_info=None):
            nonlocal status_code_out, content_length
            status_code_out = status_code
            for header, val in response_headers:
                if header.lower() == 'content-length':
                    content_length = int(val)
                    break
            return start_response(status_code, response_headers, exc_info)
        rv = self.wsgi_app(environ, wrapped_start_response)
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(self.format(environ, status_code_out, content_length, elapsed_time))
        return rv
