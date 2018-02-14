# -*- coding: utf-8 -*-
"""
    Gunicorn config.
"""
worker_class = 'sanic.worker.GunicornWorker'
bind = 'unix:/uwsgi/synergy.sock'
workers = 1
timeout = 30
max_requests = 100
daemon = False
umask = '91'
user = 'nobody'
loglevel = 'info'
