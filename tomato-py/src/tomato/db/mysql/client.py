# -*- coding:utf-8 -*-
'''
Created on 2020年11月3日

@author: zhaojiangang
'''
from twisted.enterprise import adbapi
from twisted.internet import defer

from tomato.core.future import TTFuture
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog


class TTMysqlClient(object):
    def __init__(self, conn):
        self.conn = conn
        self._keepCount = 0
        self._keepAliveTimer = TTTaskletTimer.runForever(30, self._doKeepAlive)
        self.useCount = 0

    def close(self):
        try:
            self.conn.close()
        except:
            ttlog.error('TTMysqlClient.close')
        ttlog.info('TTMysqlClient.close')

    def runWithConnection(self, func, *args, **kw):
        d = self.conn.runWithConnection(func, *args, **kw)
        if isinstance(d, defer.Deferred):
            return TTFuture(d).get()
        return d
    
    def runInteraction(self, interaction, *args, **kw):
        d = self.conn.runInteraction(interaction, *args, **kw)
        if isinstance(d, defer.Deferred):
            return TTFuture(d).get()
        return d
    
    def runQuery(self, *args, **kw):
        d = self.conn.runQuery(*args, **kw)
        if isinstance(d, defer.Deferred):
            return TTFuture(d).get()
        return d
    
    def runOperation(self, *args, **kw):
        d = self.conn.runOperation(*args, **kw)
        if isinstance(d, defer.Deferred):
            return TTFuture(d).get()
        return d
    
    def _doKeepAlive(self):
        if ttlog.isTraceEnabled():
            ttlog.trace('TTMysqlClient._doKeepAlive')
        self._keepCount += 1
        self.conn.runQuery('select %s' % (self._keepCount))


def _connectMysql(host, port, dbName, userName, password, charset='utf8mb4'):
    conn = adbapi.ConnectionPool('pymysql', db=dbName, user=userName,
                                 passwd=password, host=host, port=port,
                                 charset=charset, use_unicode=True, cp_reconnect=True,
                                 cp_min=1, cp_max=1)
    return TTMysqlClient(conn)


class TTMysqlClientCluster(object):
    def __init__(self, host, port, dbName, userName, password, charset='utf8mb4', minCount=3, maxCount=5):
        self.host = host
        self.port = port
        self.dbName = dbName
        self.userName = userName
        self.password = password
        self.charset = charset
        self.minCount = minCount
        self.maxCount = maxCount
        self.curIndex = 0
        self.clients = []

    @property
    def clientCount(self):
        return len(self.clients)

    def start(self):
        assert(len(self.clients) == 0)
        try:
            for _ in xrange(self.minCount):
                self._newClient()
        except:
            self.close()
            raise
    
    def close(self):
        clients = self.clients
        self.clients = []
        try:
            for client in clients:
                client.close()
        except:
            pass
        
    def runWithConnection(self, func, *args, **kw):
        client = self._getClient()
        try:
            d = client.runWithConnection(func, *args, **kw)
            if isinstance(d, defer.Deferred):
                return TTFuture(d).get()
            return d
        finally:
            self._releaseClient(client)
    
    def runInteraction(self, interaction, *args, **kw):
        client = self._getClient()
        try:
            d = client.runInteraction(interaction, *args, **kw)
            if isinstance(d, defer.Deferred):
                return TTFuture(d).get()
            return d
        finally:
            self._releaseClient(client)
    
    def runQuery(self, *args, **kw):
        client = self._getClient()
        try:
            d = client.runQuery(*args, **kw)
            if isinstance(d, defer.Deferred):
                return TTFuture(d).get()
            return d
        finally:
            self._releaseClient(client)
    
    def runOperation(self, *args, **kw):
        client = self._getClient()
        try:
            d = client.runOperation(*args, **kw)
            if isinstance(d, defer.Deferred):
                return TTFuture(d).get()
            return d
        finally:
            self._releaseClient(client)
    
    def _findMinClient(self):
        minClient = self.clients[0]
        for i in range(1, self.clientCount):
            client = self.clients[i]
            if client.useCount < minClient.useCount:
                minClient = client
        if ttlog.isTraceEnabled():
            ttlog.trace('TTMysqlClientCluster._findMinClient',
                        'useCount=', minClient.useCount)
        return minClient

    def _getClient(self):
        client = self._findMinClient()
        client.useCount += 1
        if ttlog.isTraceEnabled():
            ttlog.trace('TTMysqlClientCluster._getClient',
                        'client=', id(client),
                        'useCount=', client.useCount)
        return client

    def _releaseClient(self, client):
        client.useCount -= 1
        if ttlog.isTraceEnabled():
            ttlog.trace('TTMysqlClientCluster._releaseClient',
                        'client=', id(client),
                        'useCount=', client.useCount)

    def _newClient(self):
        client = _connectMysql(self.host, self.port, self.dbName,
                               self.userName, self.password, self.charset)

        self.clients.append(client)
        
        ttlog.info('TTMysqlClientCluster._newClient',
                   'host=', self.host,
                   'port=', self.port,
                   'dbName=', self.dbName,
                   'userName=', self.userName)


def connectMysql(host, port, dbName, userName, password, charset='utf8mb4', minCount=3, maxCount=5):
    conn = TTMysqlClientCluster(host, port, dbName, userName, password, charset, minCount, maxCount)
    conn.start()
    return conn

def closeMysql(conn):
    conn.conn.close()

def connectMysqlCluster(confList):
    connList = []
    try:
        for conf in confList:
            conn = connectMysql(conf['host'], conf['port'], conf['db'], conf['userName'], conf['password'])
            connList.append(conn)
        return connList
    except:
        for conn in connList:
            closeMysql(conn)
        raise


