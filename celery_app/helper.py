# coding:utf-8
import hashlib

from celery_app.config import db_host, db_passwd, db_port, db_user, db_charset, db_name
import pymysql
from datetime import datetime, timezone, timedelta


def db_create_table():
    """
    CREATE TABLE `caches` (
      `key` char(40) NOT NULL,
      `url` varchar(128) NOT NULL,
      `fullname` varchar(64) NOT NULL,
      `hits_number` int(11) NOT NULL DEFAULT '0',
      `last_hit` int(11) NOT NULL DEFAULT '0',
      `redirect_path` varchar(64) NOT NULL,
      `add_time` int(11) NOT NULL,
      PRIMARY KEY (`key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """
    pass


def get_conn():
    """
    Table: caches
    Columns:
    key	char(40) PK
    url	varchar(128)
    fullname	varchar(64)
    hits_number	int(11)
    last_hit	int(11)
    redirect_path	varchar(64)
    add_time	int(11)
    """
    conn = pymysql.connect(db=db_name,
                           host=db_host,
                           port=db_port,
                           user=db_user,
                           password=db_passwd,
                           charset=db_charset)
    return conn


def db_get_one(sql):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
    except Exception as e:
        print('error: {}-{}'.format(type(e), e))
        conn.rollback()
        result = ()
    finally:
        conn.close()
    return result


def db_execute(sql):
    conn = get_conn()
    success = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
        success = 1
    except Exception as e:
        print('error: {}-{},sql:{}'.format(type(e), e, sql))
        conn.rollback()
    finally:
        conn.close()
    return success


def get_timestamp_utcnow():
    return int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())


def get_dt_from_utc_timestamp(ts):
    return datetime.utcfromtimestamp(ts) + timedelta(hours=8)


def get_hash(s):
    hash = hashlib.sha1()
    hash.update(s.encode('utf-8'))
    return hash.hexdigest()
