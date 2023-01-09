# -*- coding:utf-8 -*-
'''
Created on 2017年5月19日

@author: zhaojiangang
'''
from twisted.internet import defer
from twisted.internet.protocol import ReconnectingClientFactory
from tomato.txredis.client import RedisClient, RedisSubscriber

from tomato.core import reactor
from tomato.core.future import TTFuture
from tomato.utils import ttlog
from tomato.core.timer import TTTaskletTimer


class TTRedisClientFactory(ReconnectingClientFactory):
    protocol = RedisClient

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._client = None
        self._deferred = defer.Deferred()
        self._kwargs = kwargs
        self._password = self._kwargs.pop('password', None)
        self._db = self._kwargs.pop('db', None)
        self._keepAliveTimer = TTTaskletTimer.forever(30, self._doKeepAlive)

    def _doKeepAlive(self):
        if ttlog.isTraceEnabled():
            ttlog.trace('TTRedisClientFactory._doKeepAlive')
        self._client.send('TIME')
    
    def buildProtocol(self, addr):
        def fire(res):
            if self._password:
                self.send('AUTH', self._password)
            if self._db:
                self.send('SELECT', self._db)
            self._deferred.callback(self)
            self._deferred = defer.Deferred()
        self._client = self.protocol(*self._args, **self._kwargs)
        self._client.factory = self
        TTTaskletTimer.runOnce(0, fire, None)
        self.resetDelay()
        self._keepAliveTimer.start()
        return self._client

    def send(self, *args):
        d = self._client.send(*args)
        if isinstance(d, defer.Deferred):
            return TTFuture(d).get()
        return d


class TTRedisLuaableConnection(object):
    def __init__(self, connection):
        # 所有connection
        self._connection = connection
        # map<luaName, shaval>
        self._luaMap = {}
    
    def loadLuaScript(self, luaName, luaScript):
        shaval = self._luaMap.get(luaName)
        if not shaval:
            shaval = self._connection.send('script', 'load', luaScript)
            self._luaMap[luaName] = shaval
        
    def executeLua(self, luaName, *args):
        shaval = self._luaMap.get(luaName)
        return self._connection.send('evalsha', shaval, *args)
    
    def send(self, *args):
        return self._connection.send(*args)


class TTRedisSubscriberProtocol(RedisSubscriber):
    def connectionMade(self):
        super(TTRedisSubscriberProtocol, self).connectionMade()
        for ch, _ in self.factory._handlers.iteritems():
            self.subscribe(ch)
        
    def messageReceived(self, channel, message):
        self.factory._onMessage(channel, message)


class TTRedisSubscriberFactory(TTRedisClientFactory):
    protocol = TTRedisSubscriberProtocol
    
    def __init__(self, *args, **kw):
        TTRedisClientFactory.__init__(self, *args, **kw)
        # map<channel, handler>
        self._handlers = {}

    def subscribe(self, channel, handler):
        assert(channel not in self._handlers)
        assert(callable(handler))
        self._handlers[channel] = handler
        self._client.subscribe(channel)

    def unsubscribe(self, channel):
        try:
            del self._handlers[channel]
        except KeyError:
            pass
        self._client.unsubscribe(channel)

    def _onMessage(self, channel, message):
        handler = self._handlers.get(channel)
        if handler:
            handler(channel, message)
    

class TTRedisPool(object):
    def __init__(self):
        self._redis = {}
        self._subscribers = {}
    
    def getRedis(self, host, port, db, timeout):
        key = (host, port, db)
        r = self._redis.get(key)
        if not r:
            r = TTRedisClientFactory(db=db)
            reactor.connectTCP(host, port, r, timeout)
            TTFuture(r.deferred).get(timeout)
            self._redis[key] = r
        return r

    def getSubscriber(self, host, port, db, timeout):
        key = (host, port, db)
        r = self._subscribers.get(key)
        if not r:
            r = TTRedisSubscriberFactory(db=db)
            reactor.connectTCP(host, port, r, timeout)
            TTFuture(r.deferred).get(timeout)
            self._subscribers[key] = r
        return r


def closeRedis(conn):
    conn.stopTrying()
    if conn.client:
        conn.client.transport.loseConnection()


def connectRedis(host, port, db, password=None, timeout=30, maxDelay=3):
    ttlog.info('connectRedis',
               'host=', host,
               'port=', port,
               'db=', db,
               'password=', password)
    conn = TTRedisClientFactory(db=db, password=password)
    conn.maxDelay = maxDelay
    reactor.connectTCP(host, port, conn, timeout=timeout)
    TTFuture(conn._deferred).get(timeout)
    return conn


def connectRedisCluster(confList, timeout, maxDelay):
    connList = []
    try:
        for conf in confList:
            conn = connectRedis(conf['host'], conf['port'], conf['db'], conf.get('password'), timeout, maxDelay)
            connList.append(conn)
        return connList
    except:
        for conn in connList:
            closeRedis(conn)
        raise


def connectSubscriber(host, port, db, password=None, timeout=30, maxDelay=3):
    ttlog.info('connectSubscriber',
               'host=', host,
               'port=', port,
               'db=', db,
               'password=', password)
    conn = TTRedisSubscriberFactory(db=db, password=password)
    conn.maxDelay = maxDelay
    reactor.connectTCP(host, port, conn, timeout=timeout)
    TTFuture(conn._deferred).get(timeout)
    return conn


