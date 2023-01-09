# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty import dao
from fqparty.dao.map_dao import MapDao
from fqparty.dao.redis.dao_redis import MapDaoRedis
from fqparty.domain.services.room_service import RoomService
from tomato.utils import ttlog


class HttpServer(object):
    pass

def initServer():
    ttlog.info('http.initServer')

def startServer():
    ttlog.info('http.startServer')


