"""Server config must keep in-process metric counters monotonic.

New file: new module under test (backend/gunicorn.conf.py) and a different
fixture shape (a real gunicorn subprocess, not the Flask test client).

Regression for the 2-worker bug: each worker exported its own OTel counters
on /metrics, scrapes alternated between them, Prometheus saw ~54 resets an
hour and rate() reported ~7,700 req/s. This boots gunicorn with the real
config file and checks every request lands on one shared counter.
"""
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
CONF = BACKEND / "gunicorn.conf.py"

pytest.importorskip("gunicorn")

# (row id, total requests, client threads)
CASES = [
    # Sequential scrapes, like Prometheus every 15s. With workers=2 these
    # alternate between per-worker counters and go backwards.
    ("sequential-scrapes-never-go-backwards", 40, 1),
    # Concurrent requests must still share one counter (threads, not
    # processes, provide the concurrency).
    ("concurrent-requests-share-one-counter", 80, 8),
]


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        value, pid = r.read().decode().split()
        return int(value), int(pid)


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "gunicorn", "-c", str(CONF),
         "--bind", f"127.0.0.1:{port}",  # CLI overrides the conf bind
         "--chdir", str(BACKEND / "tests"), "wsgi_counter:app"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + 15
    while True:
        try:
            _get(url)
            break
        except OSError:
            if proc.poll() is not None or time.monotonic() > deadline:
                proc.kill()
                pytest.fail("gunicorn did not start with gunicorn.conf.py")
            time.sleep(0.1)
    # Let every worker finish booting so a multi-worker config cannot
    # pass by luck of only one worker being up.
    time.sleep(1.5)
    yield url
    proc.terminate()
    proc.wait(timeout=10)


def test_counters_monotonic_under_server_config(server):
    failures = []
    for case_id, total, threads in CASES:
        if threads == 1:
            results = [_get(server) for _ in range(total)]
            values = [v for v, _ in results]
            backwards = [(a, b) for a, b in zip(values, values[1:]) if b <= a]
            if backwards:
                failures.append(f"{case_id}: counter went backwards at {backwards[:3]}")
        else:
            with ThreadPoolExecutor(threads) as pool:
                results = list(pool.map(lambda _: _get(server), range(total)))
            values = sorted(v for v, _ in results)
            # One shared counter -> values are unique and contiguous.
            if values != list(range(values[0], values[0] + total)):
                failures.append(f"{case_id}: duplicate/missing values, per-worker counters?")
        pids = {p for _, p in results}
        if len(pids) != 1:
            failures.append(f"{case_id}: served by {len(pids)} processes {sorted(pids)}")
    assert not failures, "\n".join(failures)
