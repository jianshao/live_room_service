# -*- coding=utf-8 -*-
'''
Created on 2017年11月20日

@author: zhaojiangang
'''

import time
import uuid

from tomato.config import configure
from tomato.conn.message import TTSessionInfo
from tomato.conn.session import TTSession
from tomato.const import ConnLostReason
from tomato.core import reactor
from tomato.core.exceptions import TTException
from tomato.core.tasklet import TTTasklet
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog


class TTConnectionServer(object):
    def __init__(self, app, conf):
        # 进程Id
        self.app = app
        # 配置
        self.conf = conf
        # 所有监听的端口
        self.listenings = []
        connConf = configure.loadJson('server.tomato.global', {}).get('conn', {})
        # 空闲的session超时时间
        self.emptyTimeout = connConf.get('emptyTimeout', 10)
        # self.conf.get('emptyTimeout', 10)
        # 心跳超时时间
        self.heartTimeout = connConf.get('heartTimeout', 30)
        # 超时检查时间
        self.checkInterval = connConf.get('checkInterval', 6)
        # 定时检查空闲的和超时的session
        self._timer = TTTaskletTimer.forever(self.checkInterval, self._processTimeout)

    @property
    def maxConnection(self):
        return self.conf.get('maxConnection', 5000)
    
    def start(self):
        listenings = self.conf.get('listenings')
        assert(listenings and isinstance(listenings, dict))
        for proto, lconf in listenings.iteritems():
            f = self.app.socketServerFactoryFactory.newSocketServerFactory(self, proto, lconf)
            if f:
                l = reactor.listenTCP(lconf['port'], f, lconf.get('backlog', 500), lconf.get('host', ''))
                self.listenings.append(l)
            else:
                raise TTException(-1, 'Unsupported proto %s' % (proto))
            
            ttlog.info('TTConnectionServer.start',
                       'proto=', proto,
                       'conf=', lconf)
        self._timer.start()
        ttlog.info('TTConnectionServer.start ok',
                   'proto=', proto,
                   'conf=', lconf,
                   'emptyTimeout=', self.emptyTimeout,
                   'heartTimeout=', self.heartTimeout,
                   'checkInterval=', self.checkInterval)
    
    def stop(self):
        self._timer.cancel()
        for l in self.listenings:
            l.stopListening()
        self.listenings = []
    
    def _onConnectionOpen(self, conn):
        try:
            sessionId = uuid.uuid1().get_hex()
            session = TTSession(self, sessionId, conn)
            self.app.sessionManager.addSession(session)
            conn.userData = session
            session.open()
            conn.resumeProducing()
            ttlog.info('TTConnectionServer.onConnectionOpen',
                       'peer=', conn.getPeer())
        except:
            ttlog.error('TTConnectionServer.onConnectionOpen',
                        'peer=', conn.getPeer())
            conn.abort()

    def onConnectionOpen(self, conn):
        conn.pauseProducing()
        TTTasklet.createTasklet(self._onConnectionOpen, conn)
    
    def _onConnectionDataReceived(self, conn, data):
        ttlog.info('TTConnectionServer._onConnectionDataReceived',
                   'peer=', conn.getPeer(),
                   'dataLen=', len(data),
                   'session=', conn.userData)
        try:
            session = conn.userData
            if session:
                session.onConnectionDataReceived(data)
        except:
            ttlog.error('TTConnectionServer._onConnectionDataReceived',
                        'peer=', conn.getPeer())
            conn.abort()

    def onConnectionDataReceived(self, conn, data):
        TTTasklet.createTasklet(self._onConnectionDataReceived, conn, data)

    def _onConnectionLost(self, conn, reason):
        ttlog.info('TTConnectionServer._onConnectionLost',
                   'peer=', conn.getPeer(),
                   'reason=', reason)
        session, conn.userData = conn.userData, None
        if session:
            self.app.sessionManager.removeSession(session)
            session.onConnectionLost(reason)

    def onConnectionLost(self, conn, reason):
        TTTasklet.createTasklet(self._onConnectionLost, conn, reason)

    def handleMessage(self, session, msg):
        serverType = self.app.routeController.serverTypeForRoute(msg.route)
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnectionServer.handleMessage',
                        'serverType=', serverType,
                        'route=', msg.route,
                        'msg=', msg.body)

        if not serverType:
            ttlog.error('Unknown route %s for session %s', msg.route, session.sessionId)
            return

        sessionInfo = TTSessionInfo(self.app.serverId, session.sessionId, session.conn.getClientIp(), session.userId)
        
        if serverType == self.app.serverType:
            resp = self.app.messageController.handleMessage(msg, sessionInfo)
        else:
            serverId = self.app.routeController.routeByServerType(serverType, msg, sessionInfo)
            resp = self.app.rpcCall(serverId, 'tomato.remote.backend.message_remote', 'forwardMessage', msg.toDict(), sessionInfo.toDict())

        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnectionServer.handleMessage',
                        'serverType=', serverType,
                        'route=', msg.route,
                        'resp=', resp,
                        'needResponse=', msg.needResponse)
        
        if msg.needResponse:
            session.sendMessage(msg.makeResponse(resp))

    def _processTimeout(self):
        # 处理emptySession
        curTime = time.time()
        
        sessionIds = []

        for session in self.app.sessionManager.sessionMap.values():
            if session.userId:
                timeout = self.heartTimeout
                lastTime = session.lastHeartbeatTime
            else:
                timeout = self.emptyTimeout
                lastTime = session.connectTime
            if curTime >= lastTime + timeout:
                sessionIds.append(session.sessionId)
                session.clientHeartbeatTimeout = True

        for sessionId in sessionIds:
            self.app.sessionManager.kickSession(sessionId, None, ConnLostReason.CONN_TIMEOUT)

        ttlog.info('TTConnectionServer._processTimeout',
                   'curTime=', curTime,
                   'timeoutCount=', len(sessionIds),
                   'sessionCount=', self.app.sessionManager.sessionCount)
    

