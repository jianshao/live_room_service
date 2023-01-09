# -*- coding:utf-8 -*-
'''
Created on 2017年11月11日

@author: zhaojiangang
'''
from tomato.rpc.exceptions import TTRPCNoSuchServiceException, \
    TTRPCNoSuchMethodException


class TTRPCService(object):
    def __init__(self):
        # key=methodName, value=method
        self._methodMap = {}

    def addMethod(self, method, name=None):
        assert(callable(method))
        name = name or method.__name__
        assert(not self.findMethod(method.__name__))
        self._methodMap[name] = method
        return self
    
    def findMethod(self, name):
        return self._methodMap.get(name)


class TTRPCRootService(object):
    def __init__(self):
        self._serviceMap = {}
        
    def findService(self, name):
        return self._serviceMap.get(name)
    
    def addService(self, name, service):
        assert(isinstance(service, TTRPCService))
        assert(not self.findService(name))
        self._serviceMap[name] = service
    
    def addMethod(self, serviceName, method, name=None):
        self._findOrCreateService(serviceName).addMethod(method, name)
    
    def call(self, serviceName, methodName, *args):
        service = self.findService(serviceName)
        if not service:
            raise TTRPCNoSuchServiceException()
        method = service.findMethod(methodName)
        if not method:
            raise TTRPCNoSuchMethodException()
        return method(*args)
    
    def _findOrCreateService(self, name):
        service = self.findService(name)
        if not service:
            service = TTRPCService()
            self._serviceMap[name] = service
        return service


