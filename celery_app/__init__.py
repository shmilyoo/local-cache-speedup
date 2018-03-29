# coding:utf-8

from celery import Celery

app = Celery('ovs')
app.config_from_object('celery_app.config.CeleryConfig')
