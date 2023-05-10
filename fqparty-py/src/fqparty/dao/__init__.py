# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''

# map<name, connList>
from tomato.config import configure
from tomato.db.mysql import client as mysqlClient
from tomato.db.redis import client as redisClient
from tomato.utils import ttlog

_namedRedisConnMap = {}
_namedMysqlConnMap = {}
_namedMqChannelMap = {}


def _getOrConnRedis(dbName):
    connList = _namedRedisConnMap.get(dbName)
    if not connList:
        conf = configure.loadJson('server.fqparty.redis', {})
        confList = conf.get(dbName)
        connList = redisClient.connectRedisCluster(confList, 3, 3)
        if not connList:
            ttlog.error('connect redis failed, config = ', connList)
        _namedRedisConnMap[dbName] = connList
    return connList


def getRedisConns(dbName):
    return _getOrConnRedis(dbName)


def _getOrConnMysql(dbName):
    connList = _namedMysqlConnMap.get(dbName)
    if not connList:
        conf = configure.loadJson('server.fqparty.mysql', {})
        confList = conf.get(dbName)
        connList = mysqlClient.connectMysqlCluster(confList)
        _namedMysqlConnMap[dbName] = connList
    return connList


def getMysqlConns(dbName):
    return _getOrConnMysql(dbName)


def _getChannel(channelName):
    mqConf = _namedMqChannelMap.get(channelName)
    if not mqConf:
        conf = configure.loadJson('server.fqparty.mq', {})
        mqConf = conf.get(channelName)
        if mqConf:
            _namedMqChannelMap[channelName] = mqConf
    return mqConf


def getMqChannelConf(channelName):
    return _getChannel(channelName)
