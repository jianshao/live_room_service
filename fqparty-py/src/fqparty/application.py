# -*- coding:utf-8 -*-
'''
Created on 2020年9月18日

@author: zhaojiangang
'''
import importlib

from fqparty import router, dao
from fqparty.conn.factory import SocketServerFactoryFactoryFQ
from fqparty.const import ServerTypes
from fqparty.domain.models.user import UserFrontDao
from fqparty.dao.redis.dao_redis import UserFrontDaoRedis, DaoRedis
from fqparty.domain.services.impl.keyword_service_impl import KeywordServiceImpl
from fqparty.domain.services.impl.util_service_impl import UtilServiceImpl
from fqparty.domain.services.keyword_service import KeywordService
from fqparty.domain.services.util_service import UtilService
from tomato import config
import tomato
from tomato.decorator import decorator
from tomato.event.event import TTServerHeartbeatEvent
from tomato.utils import ttlog
from tomato.utils.obser import TTObservable


class Application(TTObservable):
    def __init__(self):
        super(Application, self).__init__()
        # 
        self.utilService = UtilService()
        # 关键词过滤
        self.keywordService = KeywordService()
        self.userFrontDao = UserFrontDao()

    def init(self):
        # 初始化配置
        self._initConf()
        # 初始化服务
        self._initServices()
        # 初始化所有server
        self._initServers()
        
        tomato.app.socketServerFactoryFactory = SocketServerFactoryFactoryFQ()
        ttlog.info('Application.init ok')
    
    def start(self):
        self._startServers()
        
        ttlog.info('Application.start ok')
    
    def _initConf(self):
        pass

    def _initServices(self):
        sessionConn = dao.getRedisConns('session')[0]
        commonConn = dao.getRedisConns('common')[0]
        
        self.userFrontDao = UserFrontDaoRedis(DaoRedis(dao.getRedisConns('users')))
        
        self.utilService = UtilServiceImpl(sessionConn, commonConn)

        keywoardFilterUrl = config.configure.loadJson('server.fqparty.global', {}).get('keywordFilterUrl')
        if not keywoardFilterUrl:
            ttlog.warn('Application._initServices keywoardFilterUrl not configure')
        self.keywordService = KeywordServiceImpl(keywoardFilterUrl)

    def _initServers(self):
        # 设置routeFunc
        tomato.app.routeController.setRouteFuncByServerType(ServerTypes.USER, router.routeUser)
        tomato.app.routeController.setRouteFuncByServerType(ServerTypes.ROOM, router.routeRoom)
        tomato.app.routeController.setRouteFuncByServerType(ServerTypes.MIC, router.routeMic)
        # 加载handlers
        self._loadServerPackage('fqparty.servers')
    
    def _startServers(self):
        self._startServerPackage('fqparty.servers')
        
        # 监听心跳
        tomato.app.on(TTServerHeartbeatEvent, self._onServerHeartbeat)
    
    def _onServerHeartbeat(self, event):
        if event.heartbeatCount % 6 == 0:
            ttlog.info('Application._onServerHeartbeat',
                       'heartCount=', event.heartbeatCount)
    
    def _loadServerPackage(self, pkgName):
        decorator.loadServerPackageDecorator(tomato.app, pkgName)
        for serverType, subPkgName in decorator.listSubPackages(pkgName):
            if serverType == tomato.app.serverType:
                pkg = importlib.import_module(subPkgName)
                if hasattr(pkg, 'initServer'):
                    pkg.initServer()
    
    def _startServerPackage(self, pkgName):
        for serverType, subPkgName in decorator.listSubPackages(pkgName):
            if serverType == tomato.app.serverType:
                pkg = importlib.import_module(subPkgName)
                if hasattr(pkg, 'startServer'):
                    pkg.startServer()


