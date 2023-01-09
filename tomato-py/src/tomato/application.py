# -*- coding=utf-8 -*-
'''
Created on 2017年12月16日

@author: zhaojiangang
'''
from tomato.agent.base import TTAgentDelegate, TTAgentMsgTypes, TTAgent
from tomato.agent.redisps import TTAgentTransportFactoryRedisPubsub
from tomato.config import configure
from tomato.conn.factory import TTSocketServerFactoryFactoryDefault
from tomato.conn.message import TTMessageController
from tomato.conn.server import TTConnectionServer
from tomato.conn.session import TTSessionManager, TTSessionListener
from tomato.core.timer import TTTaskletTimer
from tomato.decorator import decorator
from tomato.http.http import TTHttpRequestController, TTHttpServer
from tomato.router.router import TTRouterController
from tomato.rpc.rpc import TTRPC
from tomato.rpc.service import TTRPCRootService
from tomato.utils import ttlog
from tomato.utils.obser import TTObservable
from tomato.event.event import TTServerHeartbeatEvent
from tomato.core.tasklet import TTTasklet


class TTApplication(TTObservable, TTAgentDelegate):
    def __init__(self):
        self.serverId = None
        self.serverType = None
        self.agentMap = {}
        self.serverMap = {}
        # map<serverType, list<serverInfo> >
        self.typedServerMap = {}

        self.serverInfo = None
        self.agentInfo = None
        self.rpc = None
        self.agent = None
        self.sessionListener = TTSessionListener()
        self.routeController = TTRouterController(self)
        self.sessionManager = TTSessionManager(self)
        self.messageController = TTMessageController()
        self.httpController = TTHttpRequestController()
        self.rootService = TTRPCRootService()
        self.socketServerFactoryFactory = TTSocketServerFactoryFactoryDefault()

        self._heartbeatCount = 0
        self._heartbeatTimer = TTTaskletTimer.forever(1, self._onHeartbeat)
        self.appArgs = []

    def getServerInfosByServerType(self, serverType):
        return self.typedServerMap.get(serverType)

    def getServerInfoByServerId(self, serverId):
        return self.serverMap.get(serverId)

    def init(self, serverId):
        self.serverId = serverId
        machineInfos = configure.loadJson('server.tomato.machines', {})
        agentInfos = configure.loadJson('server.tomato.agents', {})
        typedServerInfos = configure.loadJson('server.tomato.servers', {})

        for agentInfo in agentInfos:
            self.agentMap[agentInfo['agentId']] = dict(agentInfo)

        for serverType, serverInfos in typedServerInfos.iteritems():
            serverInfoList = []
            self.typedServerMap[serverType] = serverInfoList
            for serverInfo in sorted(serverInfos, key=lambda s:s['serverId']):
                si = dict(serverInfo)
                si['serverType'] = serverType
                machineName = si['machine']
                machine = machineInfos[machineName]
                si['machine'] = machine
                serverInfoList.append(si)
                self.serverMap[serverInfo['serverId']] = si

        ttlog.info('serverMap=', self.serverMap)
        ttlog.info('typedServerMap=', self.typedServerMap)
        self.serverInfo = self.serverMap[self.serverId]
        self.serverType = self.serverInfo['serverType']
        self.agentInfo = self.agentMap[self.serverInfo['agentId']]
        self.agent = TTAgent(self.serverId, self.agentInfo, TTAgentTransportFactoryRedisPubsub(), self)
        for agentId, agentInfo in self.agentMap.iteritems():
            self.agent.addAgent(agentId, agentInfo)

        self.rpc = TTRPC(self.agent, self.rootService)

        decorator.loadSystemRemote(self, 'tomato.common.remote')

    def start(self):
        self.agent.start()

        conf = self.serverInfo.get('http')
        if conf:
            self.httpServer = TTHttpServer(self.httpController, conf)
            self.httpServer.start()

        conf = self.serverInfo.get('frontend')
        if conf:
            self.connServer = TTConnectionServer(self, conf)
            self.connServer.start()

        self._heartbeatTimer.start()

        ttlog.info('TTApp.start ok')

    def isFrontend(self):
        return self.serverInfo.get('frontend') is not None

    def rpcCall(self, targetId, service, method, *args, **kw):
        '''
        调用远程服务
        @param targetId: 远程进程ID
        @param service: 远程服务名称
        @param method: 远程服务的方法名
        @param args: 方法的参数
        @param kw: 目前支持timeout表示超时时间，如果不设置用默认的, block=1表示阻塞，默认=1
        @return: 如果block=1则返回回应，否则返回TTFuture对象
        '''
        return self.rpc.call(targetId, service, method, *args, **kw)

    def rpcPost(self, targetId, service, method, *args):
        '''
        调用远程方法，不需要回应
        @param targetId: 目标服务器ID
        @param service: 要调用的服务名称
        @param method: 要调用的服务中的方法
        @param args: 参数
        '''
        return self.rpc.post(targetId, service, method, *args)

    def registerMessageHandler(self, route, handler):
        '''
        注册消息处理器
        @param route: 消息路由，字符串
        @param handler: 处理函数 def messageHandler(msg)
        @return: 处理返回结果
        '''
        self.messageController.addHandler(route, handler)

    def registerRemoteMethod(self, serviceName, method, methodName=None):
        '''
        注册远程方法
        @param serviceName: 服务名称
        @param method: 方法或者函数
        @param methodName: 方法名称如果为None则用method.__name__作为方法名称
        @return: 处理返回结果
        '''
        self.rootService.addMethod(serviceName, method, methodName)

    def registerHttpHandler(self, path, handler):
        '''
        注册http请求处理器
        @param path: uri
        @param handler: 处理器 def httpHandler(request)
        @return:
        '''
        self.httpController.addHandler(path, handler)

    def routeByServerId(self, agent, serverId):
        si = self.serverMap.get(serverId)
        if not si:
            return None
        return si['agentId']

    def handleAgentMessage(self, agent, sourceId, msgType, msg):
        if msgType == TTAgentMsgTypes.RPC:
            self.rpc.handleRpcMessage(agent, sourceId, msg)
        else:
            ttlog.warn('TTApplication.handleAgentMessage UnknownMsgType',
                       'sourceId=', sourceId,
                       'msgType=', msgType,
                       'msgLen=', len(msg))

    def _onHeartbeat(self):
        self._heartbeatCount += 1

        if ttlog.isDebugEnabled():
            ttlog.debug('TTApplication._onHeartbeat',
                        'heartCount=', self._heartbeatCount,
                        'taskletCount=', TTTasklet.taskletCount())

        self.fire(TTServerHeartbeatEvent(self._heartbeatCount))


