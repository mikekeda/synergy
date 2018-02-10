# -*- coding: utf-8 -*-
"""
    Gunicorn config..
"""
bind = 'unix:/uwsgi/synergy.sock'
workers = 1
timeout = 30
max_requests = 100
daemon = False
umask = '644'
user = 'nobody'
loglevel = 'info'
