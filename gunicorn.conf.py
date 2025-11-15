# gunicorn.conf.py
bind = "0.0.0.0:8080"
workers = 1  # Reduce from 3 to 1 for free tier
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100