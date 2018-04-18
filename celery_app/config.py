# coding:utf-8

# from datetime import timedelta
# from celery.schedules import crontab
# from kombu import Queue
# from kombu import Exchange
from celery.schedules import crontab

R_ANALYZING = 'ANALYZING'  # list
R_DOWNLOADING = 'DOWNLOADING'  # list
R_PROCESSING = 'PROCESSING'  # list
R_ARGS_PASS = 'ARGS_PASS'  # hash

cap_dst = '192.241.211.12'  # 抓包需要捕获的目的地址
cap_port = 80
cap_ext = ['mp4', 'flv']  # 抓包需要捕获的链接地址的后缀
cap_dev = 'wlp8s0'
# local_ip = '192.168.43.201'

db_name = 'video_cache'
db_host = 'localhost'
db_port = 3306
db_user = 'root'
db_passwd = 'root'
db_charset = 'utf8'

cache_threshold = 5  # the number of request to start cache
download_base = '/var/www/celery/download'
redirect_url_base = '/download'
redirect_src = '192.168.43.201'

# return true when all the condition is true
cleanup_condition = {
    'hit': 5,   # hits_number <= 5
    'no_visit': 60 * 60 * 24 * 30   # how many seconds the cache have not been hit
}


class CeleryConfig:
    broker_url = 'redis://127.0.0.1:6379/0'  # 指定 Broker
    result_backend = 'redis://127.0.0.1:6379/0'  # 指定 Backend
    timezone = 'Asia/Shanghai'  # 指定时区，默认是 UTC
    imports = ('celery_app.analyze_url_task', 'celery_app.packet_cap_task', 'celery_app.download_task',
               'celery_app.cron_task',)
    task_queues = {
        'q_pcap': {'exchange': 'celery', 'routing_key': 'rk_pcap'},
        'q_analyze': {'exchange': 'celery', 'routing_key': 'rk_analyze'},
        'q_download': {'exchange': 'celery', 'routing_key': 'rk_download'},
        'q_schedule': {'exchange': 'celery', 'routing_key': 'rk_schedule'}
    }
    task_routes = ([('celery_app.packet_cap_task.packet_cap', {'queue': 'q_pcap', 'routing_key': 'rk_pcap'}),
                    ('celery_app.analyze_url_task.analyze_url', {'queue': 'q_analyze', 'routing_key': 'rk_analyze'}),
                    ('celery_app.download_task.download', {'queue': 'q_download', 'routing_key': 'rk_download'})
                    ],)
    # schedules
    beat_schedule = {
        'cleanup-everyday': {
            'task': 'celery_app.cron_task.cleanup',
            'schedule': crontab(hour='0', minute='0'),  # cleanup every midnight
            'options': {'routing_key': 'rk_schedule', 'queue': 'q_schedule'}
            # 'args': (3, 7)  # 任务函数参数
        }
    }
