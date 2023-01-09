# -*- coding=utf-8 -*-
'''
Created on 2018年2月11日

@author: zhaojiangang
'''
import functools

from twisted.internet import defer

from tomato.core.future import TTFuture
from txmongo.connection import ConnectionPool


class _MongoConnection(ConnectionPool):
    def __init__(self, url, pool_size=1, **kwargs):
        ConnectionPool.__init__(self, url, pool_size=pool_size, **kwargs)


class TTMongoConnection(object):
    def __init__(self, url, pool_size=1, **kw):
        self.connection = _MongoConnection(url, pool_size, **kw)

    @classmethod
    def makeByHostPort(cls, host, port, pool_size=1, **kw):
        url = "mongodb://%s:%d/" % (host, port)
        return TTMongoConnection(url, pool_size, **kw)
    
    def getDatabase(self, name):
        db = self.connection[name]
        return TTMongoDatabase(db)
    
    def disconnect(self):
        self.connection.disconnect()


class TTMongoConnectionPool(object):
    def __init__(self):
        # map<host:port, TTMongoConnection>
        self._connectionMap = {}
    
    def getConnection(self, host, port):
        key = '%s:%s' % (host, port)
        conn = self._connectionMap.get(key)
        if not conn:
            conn = TTMongoConnection.makeByHostPort(host, port)
            self._connectionMap[key] = conn
        return conn


class TTMongoCollection(object):
    def __init__(self, collection):
        super(TTMongoCollection, self).__init__()
        self.__collection__ = collection
        self.__cacheItem__ = {}

    def __getattr__(self, key):
        value = self.__dict__.get(key)
        if value:
            return value
        value = self.__cacheItem__.get(key)
        if value:
            return value
        if hasattr(self.__collection__, key):
            value = getattr(self.__collection__, key)
            if callable(object):
                value = self._wrapMethod(value)
                self.__cacheItem__[key] = value
                return value
        return None
    
    def _wrapMethod(self, method):
        @functools.wraps(method)
        def _func(*args, **kw):
            r = method(*args, **kw)
            if isinstance(r, defer.Deferred):
                return TTFuture(r).get()
            return r
        return _func


class TTMongoDatabase(object):
    def __init__(self, db):
        self.db = db
    
    def getCollection(self, name):
        collection = self.db[name]
        return TTMongoCollection(collection)


def connectMongoByUrl(url, **kw):
    return TTMongoConnection(url)


def connectMongoByHostPort(host, port, **kw):
    return TTMongoConnection.makeByHostPort(host, port, **kw)


def connectMongoCluster(confList, **kw):
    connList = []
    try:
        for conf in confList:
            url = conf.get('url')
            if url:
                conn = connectMongoByUrl(url, **kw)
            else:
                conn = connectMongoByHostPort(conf['host'], conf['port'], **kw)
            connList.append(conn)
        return connList
    except:
        for conn in connList:
            conn.disconnect()
        raise


