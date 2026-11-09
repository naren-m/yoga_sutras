# Gunicorn settings for the backend container (docker/Dockerfile.backend).
#
# One worker, many threads. Metrics are kept in-process by the OTel SDK
# (homelab-observability) and served on /metrics by whichever worker takes
# the request. With 2 workers, each scrape hit a different worker's counters,
# so values jumped back and forth (~54 fake counter resets an hour) and
# rate() reported ~7,700 req/s on a pod using 4m of CPU. A single process
# keeps every counter monotonic. Concurrency comes from threads instead,
# same as ramayanam (--workers 1 --worker-class gthread --threads 8).
#
# If this ever needs more than one process, switch metrics to
# prometheus_client multiprocess mode first; do not just raise `workers`.
# tests/test_gunicorn_conf.py fails if counters stop being monotonic.

bind = "0.0.0.0:5001"
workers = 1
worker_class = "gthread"
threads = 8
timeout = 120
accesslog = "-"
errorlog = "-"
