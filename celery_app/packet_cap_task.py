# coding:utf-8
import json
import redis

try:
    from scapy.layers import http
except ImportError:
    from scapy_http import http
from celery_app import app
from scapy.all import *
from celery_app.config import cap_ext, R_ARGS_PASS, R_PROCESSING
import os
from celery_app.helper import get_hash



def prn_callback(r):
    def parse_packet(packet):
        if not packet.haslayer(http.HTTPRequest):
            return
        http_layer = packet.getlayer(http.HTTPRequest)
        if http_layer.fields['Method'] != b'GET':
            return
        ip_layer = packet.getlayer(IP)
        # path like 'http://1.1.1.1/a//b/c/d.mp4 or /a/b/c/d.mp4 or /a//b/c.mp4'
        url = http_layer.fields['Path'].decode('utf-8').replace('//', '/')
        url_low = url.lower()
        if any([url_low.endswith(ext) for ext in cap_ext]):
            # print('\n{0[src]} - {1[Method]} - http://{1[Host]}{1[Path]}'.format(ip_layer.fields, http_layer.fields))
            print('{} - {} - http://{}{}'.format(ip_layer.fields['src'].decode('utf8'),
                                                 http_layer.fields['Method'].decode('utf8'),
                                                 http_layer.fields['Host'].decode('utf8'),
                                                 http_layer.fields['Path'].decode('utf8')))
            key = get_hash(url)
            if r.sismember(R_PROCESSING, key):
                print('key {}(url {}) is now processing,skip sending it from pcap to analyze'.format(key, url))
                return
            pkt_info = get_pkt_info(packet)
            pkt_info.update({'key': key, 'url': url})
            r.hset(R_ARGS_PASS, key, json.dumps(pkt_info))
            print('send key {}(url {}) to analyze process'.format(key, url))
            app.send_task('celery_app.analyze_url_task.analyze_url', (key,))
            r.sadd(R_PROCESSING, key)

    return parse_packet


def get_pkt_info(pkt):
    mac_src = pkt[Ether].src
    mac_dst = pkt[Ether].dst
    ip_src = pkt[IP].src
    ip_dst = pkt[IP].dst
    ip_len = pkt[IP].len
    tcp_sport = pkt[TCP].sport
    tcp_dport = pkt[TCP].dport
    tcp_ack = pkt[TCP].ack
    tcp_seq = pkt[TCP].seq
    tcp_payload_len = len(pkt[TCP].payload)
    return {'mac_src': mac_src, 'mac_dst': mac_dst, 'ip_src': ip_src, 'ip_dst': ip_dst,
            'ip_len': ip_len, 'tcp_seq': tcp_seq, 'tcp_payload_len': tcp_payload_len,
            'tcp_sport': tcp_sport, 'tcp_dport': tcp_dport, 'tcp_ack': tcp_ack}


@app.task(ignore_result=True)
def packet_cap(dport, dhost, dev):
    """
    sniff(filter='tcp and dst port 80 and dst host *.*.*.*',iface='')
    """
    print('start capture at process {0}'.format(os.getpid()))
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    _filter = "dst {0} and tcp and dst port {1}".format(dhost, dport)  # not host , dst?
    sniff(iface=dev, filter=_filter, prn=prn_callback(r), store=False)
