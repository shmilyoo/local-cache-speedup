# coding:utf-8
from celery_app.helper import db_execute
import redis
from celery_app.config import download_base
import os


def clear():
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    r.flushall()
    sql = 'delete from caches;'
    db_execute(sql)
    # os.system('rm {}/* -rf'.format(download_base))
    # os.system('rm /var/log/celery/*')


if __name__ == '__main__':
    clear()
