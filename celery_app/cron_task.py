# coding:utf-8
from celery_app import app
from celery_app.helper import db_execute, get_timestamp_utcnow
from celery_app.config import cleanup_condition


@app.task(ignore_result=True)
def cleanup():
    sql = ('delete from `caches` where `hits_number` < {} and '
           '`last_hit` < {};').format(cleanup_condition['hit'], get_timestamp_utcnow() - cleanup_condition['no_visit'])
    db_execute(sql)
    print('===================clean up now===================')
