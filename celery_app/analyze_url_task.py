# coding:utf-8
# from scapy.layers.inet import IP, TCP

from celery_app import app
import redis
import json
from celery_app.helper import db_get_one, get_timestamp_utcnow, db_execute
from scapy.all import *
from celery_app.config import R_DOWNLOADING, R_ANALYZING, R_ARGS_PASS, cache_threshold, redirect_src, R_PROCESSING


@app.task(ignore_result=True)
def analyze_url(key):
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    _pkt_info = r.hget(R_ARGS_PASS, key)
    r.hdel(R_ARGS_PASS, key)
    # if r.sismember(R_ANALYZING, key) or r.sismember(R_DOWNLOADING, key):
    #     print('key {} in redis is already in analyze/download process'.format(key))
    #     return
    # if r.sismember(R_PROCESSING, key):
    #     print('key {} in redis is already in processing,skip analyze'.format(key))
    #     return
    pkt_info = json.loads(_pkt_info)
    # r.sadd(R_ANALYZING, key)
    try:
        print('analyze process get job,url is {}, key is {}'.format(pkt_info['url'], key))
        # use the hash key of url as the primary index key in db
        sql = "select `url`,`hits_number`,`redirect_path` from caches where `key` = '{}';".format(key)
        cache = db_get_one(sql)
        if cache:
            print('cache: {}'.format(cache))
            redirect = cache[2]
            if redirect:
                # the url file has aleady download
                print('the file in url {} is available for cache, '
                      'send http 302 to src host {}'.format(pkt_info['url'], pkt_info['ip_src']))
                send_http_302(redirect, pkt_info)
                # if update_lasthit_hitnumber(key):
                #     print(
                #         'update hits_number and last_hit after send http 302 for url {}'.format(pkt_info['url']))
                # else:
                #     print('some error occured with db when update hits_number and last_hit in send http 302 process')
            else:
                hit_number = cache[1]
                if hit_number >= cache_threshold:
                    print('the hit_number reach the cache_threshold,start downloading,'
                          'Send the task to download process'.format(pkt_info['url']))
                    r.hset(R_ARGS_PASS, key, _pkt_info)
                    app.send_task('celery_app.download_task.download', (key,))
                    # r.srem(R_ANALYZING, key)
                # else:
                # the record is exist,but file did not downloaded because the cache_threshold has not been reached.
                # hits_number + 1 only
                # if update_lasthit_hitnumber(key):
                #     print(
                #         'add hits_number({}) by 1 because the cache_threshold has not been reached'.format(
                #             hit_number))
                # else:
                #     print('some error occured in add hits_number,sql is {}'.format(sql))
            # hits_number + 1
            if not update_lasthit_hitnumber(key):
                print('some error occured in add hits_number,key is {}'.format(key))
        else:
            # no record exist, create the db record and  estimate the cache_threshold
            sql = 'insert into `caches` (`key`,`url`,`hits_number`,`last_hit`,`redirect_path`,`add_time`) values ("{0}","{1}",1,{2},"",{2})'.format(
                key, pkt_info['url'], get_timestamp_utcnow())
            if db_execute(sql):
                print('insert new url row, key {}(url {})'.format(key, pkt_info['url']))
            else:
                print('error happened in insert new url row, key {}(url {})'.format(key, pkt_info['url']))
            if cache_threshold == 0:
                # meet the cache_threshold although the cache does not exist. send to download process
                print('send key {}(url {}) to download process'.format(key, pkt_info['url']))
                r.hset(R_ARGS_PASS, key, _pkt_info)
                app.send_task('celery_app.download_task.download', (key,))
    except Exception as e:
        r.srem(R_PROCESSING, key)
        print('error happend in analyzing {},analyze process now end,exception is {}'.format(pkt_info['url'], e))
    # finally:
    #     r.srem(R_PROCESSING, key)


def update_lasthit_hitnumber(key):
    sql = 'update `caches` set `hits_number` = `hits_number` + 1,`last_hit` = {} where `key` = "{}"'.format(
        get_timestamp_utcnow(), key)
    return db_execute(sql)


def send_http_302(redirect, pk):
    """
    {'mac_src': '00:c2:c6:14:61:a8', 'ip_src': '192.168.43.201', 'key': 'f71e7a8514fc1efd00391a17533d22ad66ebc22a', 'mac_dst': '02:1a:11:f2:cb:10', 'ip_len': 473, 'tcp_sport': 34808, 'url': '/5M.mp4', 'tcp_dport': 80, 'tcp_ack': 433645881, 'ip_dst': '192.241.211.12'}
    """
    redirect_url = 'http://{}{}'.format(redirect_src, redirect)
    http_payload = "HTTP/1.1 302 Found\r\nLocation: %s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n" % redirect_url
    resp = IP(dst=pk['ip_src'], src=pk['ip_dst']) / TCP(dport=pk['tcp_sport'], sport=pk['tcp_dport'], flags="PA",
                                                        seq=pk['tcp_ack'],
                                                        ack=pk['tcp_seq'] + pk['tcp_payload_len']) / Raw(
        load=http_payload)
    send(resp)
