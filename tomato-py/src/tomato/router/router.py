# -*- coding=utf-8 -*-
'''
Created on 2018年1月13日

@author: zhaojiangang
'''
from tomato.core.exceptions import TTException
from tomato.utils import ttlog

class TTRouterController(object):
    def __init__(self, app):
        # 哪个应用
        self.app = app
        # map<route, ServerType>
        self.routeMap = {}
        # map<serverType, func>
        self.routeFuncMap = {}

    def serverTypeForRoute(self, route):
        serverType = self.routeMap.get(route)
        if not serverType:
            index = route.rfind('/')
            if index > 0:
                r = route[0:index + 1]
                r += '*'
                return self.routeMap.get(r)
        return serverType
    
    def setServerTypeByRoute(self, route, serverType):
        foundServerType = self.serverTypeForRoute(route)
        if foundServerType and foundServerType != serverType:
            assert(0)
        self.routeMap[route] = serverType
    
    def setRouteFuncByServerType(self, serverType, routeFunc):
        self.routeFuncMap[serverType] = routeFunc
    
    def routeByServerType(self, serverType, *args, **kw):
        func = self.routeFuncMap.get(serverType)
        if not func:
            raise TTException(-1, 'Unknown route function for serverType: %s' % (serverType))
        return func(serverType, *args, **kw)
    

