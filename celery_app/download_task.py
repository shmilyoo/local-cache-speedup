# coding:utf-8
import json
import time

from celery_app import app
import redis
from os import path

from celery_app.helper import db_execute
from celery_app.pyaria2 import PyAria2
from celery_app.config import download_base, R_ARGS_PASS, redirect_url_base,R_PROCESSING


@app.task(ignore_result=True)
def download(key):
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    _pkt_info = r.hget(R_ARGS_PASS, key)
    pkt_info = json.loads(_pkt_info)
    r.hdel(R_ARGS_PASS, key)
    # if r.sismember(R_PROCESSING, key):
    #     print('key {} url {} in redis is already processing'.format(key, pkt_info['url']))
    #     return
    # r.sadd(R_DOWNLOADING, key)
    # start downloading, send rpc message to aria2 server
    try:
        job = PyAria2()
        url = pkt_info['url']
        full_url = 'http://{}{}'.format(pkt_info['ip_dst'], url)
        # turn url, such as: '/' -> '', '/a/b/c.mp4' -> 'a/b
        sub_dir = '/'.join(url.split('/')[:-1]).lstrip('/')
        download_dir = path.join(download_base, sub_dir)
        options = {'dir': download_dir}
        id = job.addUri([full_url], options=options)
        print('start downloading {} to {},aria2 job id is {}'.format(full_url, download_dir, id))
        while True:
            status = job.tellStatus(id, ['status'])
            if status['status'] == 'complete':
                print('the download is complete,saving {} to {}'.format(full_url, options['dir']))
                if save_to_db(key, url):
                    print('has saved {} to {}'.format(full_url, options['dir']))
                else:
                    print('some error occured in saving {} to {}'.format(full_url, options['dir']))
                break
            elif status['status'] == 'error':
                print('something error happened in downloading {},the job now quit,download process now stop'.format(
                    full_url))
                break
            elif status['status'] == 'removed':
                print('the job for {} was removed,download process now stop'.format(full_url))
                break
            else:
                pass
            time.sleep(1)
    except Exception as e:
        print('Exception happend in downloading {},download process now end,exception is {}'.format(url, e))
    finally:
        r.srem(R_PROCESSING, key)


def save_to_db(key, url):
    sql = "update `caches` set `redirect_path` = '{}' where `key` = '{}';".format(
        path.join(redirect_url_base, url.lstrip('/')), key)
    return db_execute(sql)
