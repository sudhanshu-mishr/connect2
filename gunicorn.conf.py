# gunicorn.conf.py
worker_class = 'uvicorn.workers.UvicornWorker'
bind = '0.0.0.0:10000'
workers = 4
