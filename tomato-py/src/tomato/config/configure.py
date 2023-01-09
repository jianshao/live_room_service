# -*- coding=utf-8 -*-
'''
Created on 2018年5月3日

@author: zhaojiangang
'''
import os

from tomato.db.redis import client
from tomato.utils import strutil, ttlog


class TTConfiger(object):
    def init(self):
        raise NotImplementedError
    
    def loadJson(self, module, defVal=None):
        raise NotImplementedError
    
    def reloadConf(self, module):
        raise NotImplementedError


class TTAbstractConfiger(TTConfiger):
    def __init__(self):
        self._cache = {}

    def init(self):
        pass
    
    def loadJson(self, module, defVal=None):
        content = self._cache.get(module)
        if content is None:
            content = self._loadJsonImpl(module)
            if content is None:
                content = defVal
            self._cache[module] = content
        return content
    
    def reloadConf(self, module):
        if not module:
            self._cache.clear()
        else:
            self._cache.pop(module, None)
    
    def _loadJsonImpl(self, module):
        raise NotImplementedError
    

class TTConfigerFile(TTAbstractConfiger):
    def __init__(self, rootPath):
        super(TTConfigerFile, self).__init__()
        self._rootPath = rootPath
    
    def _loadJsonImpl(self, module):
        filePath = os.path.join(self._rootPath, module.replace('.', '/'))
        filePath += '.json'
        if not os.path.isfile(filePath):
            return None
        return strutil.jsonLoadFile(filePath)


class TTConfigerRedis(TTAbstractConfiger):
    def __init__(self, host, port, db, timeout=3, maxDelay=3):
        super(TTConfigerRedis, self).__init__()
        self._host = host
        self._port = port
        self._db = db
        self._timeout = timeout
        self._maxDelay = maxDelay
        self._redis = None

    def init(self):
        assert(not self._redis)
        self._redis = client.connectRedis(self._host, self._port, self._db, self._timeout, self._maxDelay)

    def _loadJsonImpl(self, module):
        jstr = self._redis.send('get', module)
        return strutil.jsonLoads(jstr)


_configer = TTConfiger()


def loadJson(module, defVal=None):
    return _configer.loadJson(module, defVal)

def reloadConf(module):
    _configer.reloadConf(module)

def initByRedis(host, port, db):
    global _configer
    ttlog.info('configure.initByRedis',
               'host=', host,
               'port=', port,
               'db=', db)
    configer = TTConfigerRedis(host, port, db, 3, 3)
    configer.init()
    _configer = configer

def initByFile(rootPath):
    global _configer
    ttlog.info('configure.initByFile',
               'rootPath=', rootPath)
    configer = TTConfigerFile(rootPath)
    configer.init()
    _configer = configer


    
