"""Tiny WSGI app for tests/test_gunicorn_conf.py.

Stands in for an in-process metrics counter: every request bumps a
module-level counter and returns the new value plus the serving PID. Run
under the real gunicorn.conf.py, it shows whether all requests see one
counter (monotonic) or several per-worker copies (values jump backwards).
"""
import itertools
import os

_counter = itertools.count(1)


def app(environ, start_response):
    body = f"{next(_counter)} {os.getpid()}".encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
