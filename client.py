# coding:utf-8
from celery_app.packet_cap_task import packet_cap
from celery_app.config import cap_dst, cap_dev, cap_port


if __name__ == '__main__':
    # sniff(iface=cap_dev, filter="tcp and dst port {0} and host {1}".format(cap_port, cap_dst), prn=test)
    # # sniff(iface=cap_dev, filter="udp", prn=lambda x: x.summary())
    # pass
    packet_cap.delay(cap_port, cap_dst, cap_dev)
