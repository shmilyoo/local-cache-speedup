# implement a local high speed cache accelerator system with celery and scapy

## celery flow chart
![流程图](https://ws1.sinaimg.cn/large/566418e8gy1fpukerjeyzj20qf0gz409.jpg)

## how to manage your workers
### workers 
be care the pidfile and logfile directory privilege
```
celery -A celery_app worker -l info -c 1 -Q q_pcap -n pcap_worker --pidfile /run/celery/pcap_worker.pid --logfile /var/log/celery/pcap_worker.log --loglevel info
celery -A celery_app worker -l info -c 2 -Q q_analyze -n analyze_worker --pidfile /run/celery/analyze_worker.pid --logfile /var/log/celery/analyze_worker.log --loglevel info
celery -A celery_app worker -l info -c 4 -Q q_download -n download_worker --pidfile /run/celery/download_worker.pid --logfile /var/log/celery/download_worker.log --loglevel info
```
or use celery multi command
```
START: celery multi start pcap analyze download -A celery_app -c:1 1 -c:2 2 -c:3 4 -Q:1 q_pcap -Q:2 q_analyze -Q:3 q_download --pidfile=/home/yy/projects/online-video-speedup/pid/%n.pid --logfile=/var/log/celery/%n.log
STOP(warm):celery multi stopwait pcap analyze download --pidfile=/home/yy/projects/online-video-speedup/pid/%n.pid
STOP(cold):celery multi stop pcap analyze download --pidfile=/home/yy/projects/online-video-speedup/pid/%n.pid
RESTART: celery multi restart pcap analyze download -A celery_app -c:1 1 -c:2 2 -c:3 4 -Q:1 q_pcap -Q:2 q_analyze -Q:3 q_download --pidfile=/home/yy/projects/online-video-speedup/pid/%n.pid --logfile=/var/log/celery/%n.log
```

#### restart workers
**use HUP signal only can stop the process. In order to restart it, you should start worker as daemon mode**
mkdir /run/celery  and change the user and group
```
cat /run/celery/pcap_worker.pid |xargs kill -HUP
cat /run/celery/analyze_worker.pid |xargs kill -HUP
cat /run/celery/download_worker.pid |xargs kill -HUP
```
## or you can manage your workers with systemd and celery multi command
[celery multi command api](http://celery.readthedocs.io/en/latest/reference/celery.bin.multi.html)  
[using systemd](http://celery.readthedocs.io/en/latest/userguide/daemonizing.html#usage-systemd)    
##### the sytemd service file:
```
[Unit]
Description=Celery-cache Service
After=network.target

[Service]
Type=forking
User=yy
Group=yy
EnvironmentFile=-/home/yy/projects/online-video-speedup/worker.conf
WorkingDirectory=/home/yy/projects/online-video-speedup
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target
```
##### and the EnvironmentFile:
```
# Name of nodes to start
# here we have a single node
#CELERYD_NODES="w1"
# or we could have three nodes:
CELERYD_NODES="pcap analyze download schedule"

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/home/yy/.virtualenvs/online-video-speedup/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="celery_app"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# How to call manage.py
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="-c:1 1 -c:2 2 -c:3 4 -c:4 1 -Q:1 q_pcap -Q:2 q_analyze -Q:3 q_download -Q:4 q_schedule"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/var/log/celery/%n.log"
CELERYD_LOG_LEVEL="INFO"
```
## flower
start flower service:

    celery -A celery_app flower
    
## beat and schedule
start beat

    celery beat -A celery_app
  or
  
    celery beat -A celery_app  -l info --pidfile ./pid/beat.pid --logfile /var/log/celery/beat.log
the worker schedule will receive the beat task according to the config

## grant scapy the privilege to cap packets

    sudo setcap cap_net_raw=eip your_python_exe
I use virtualenv here   
maybe you should execute this additional

    sudo setcap cap_net_raw=eip /usr/sbin/tcpdump

## about download and monitor
set the download base dir (absolute) in config.py  
install aria2  
the download process will auto start aria2c to download the url  
You can use [yaaw](https://github.com/binux/yaaw) to monitor the aria2 download status.