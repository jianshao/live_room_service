# -*- coding=utf-8 -*-
'''
Created on 2017年11月22日

@author: zhaojiangang
'''
import time

from tomato.conn.message import TTMessage, TTPacketTypes
from tomato.core.exceptions import TTException
from tomato.utils import ttlog
from tomato.core.timer import TTTaskletTimer
from tomato.const import ConnLostReason


class TTSessionListener(object):
    def onSessionOpened(self, session):
        pass
    
    def onSessionBindUser(self, session):
        pass
    
    def onSessionClosed(self, session, reason):
        pass
    
    def onSessionHeartbeat(self, session, pkg):
        pass


class TTSessionManager(object):
    def __init__(self, app):
        self.app = app
        # map<sessionId, TTSession>
        self._sessionMap = {}
        # map<uid, TTSession>
        self._uid2Session = {}
        
    @property
    def sessionCount(self):
        return len(self._sessionMap)

    @property
    def sessionMap(self):
        return self._sessionMap
    
    def findSession(self, sessionId):
        return self._sessionMap.get(sessionId)
    
    def findSessionByUserId(self, userId):
        return self._uid2Session.get(userId)
    
    def addSession(self, session):
        exists = self.findSession(session.sessionId)
        if exists:
            raise TTException(-1, 'Duplicate sessionId %s' % (session.sessionId))
        self._sessionMap[session.sessionId] = session

    def kickSession(self, sessionId, msg, reason=ConnLostReason.CONN_KICKOUT):
        session = self.findSession(sessionId)
        if session:
            self.removeSession(session)
            if msg:
                session.sendMessage(msg)
            if self.app.sessionListener:
                session.callListener = True
                self.app.sessionListener.onSessionClosed(session, reason)
            session.userId = 0
            session.close()
        return session
    
    def removeSession(self, session):
        s = self._sessionMap.pop(session.sessionId, None)
        if s:
            self._uid2Session.pop(session.userId, None)
            ttlog.info('Remove session', session.sessionId, session.userId, self.sessionCount)

    def bindUser(self, sessionId, userId):
        '''
        绑定用户ID
        '''
        session = self.findSessionByUserId(userId)
        if session:
            raise TTException(-1, 'User session already exists %s %s' % (session.sessionId, userId))
        
        session = self.findSession(sessionId)
        if not session:
            raise TTException(-1, 'Not found session %s %s' % (sessionId, userId))
        
        if session.userId:
            raise TTException(-1, 'Session already bind %s %s' % (session.sessionId, session.userId))
        
        self._uid2Session[userId] = session
        session.bindUser(userId)
        

class TTSession(object):
    MAX_SEND_BUFFER = 2 * 1024 * 1024
    
    def __init__(self, server, sessionId, conn):
        self.server = server
        self.sessionId = sessionId
        self.conn = conn
        self.lastHeartbeatTime = self.connectTime = time.time()
        self.userId = 0
        self.heartbeatTimer = None
        self.clientHeartbeatTimeout = False
        self._pktHandlerMap = {
            TTPacketTypes.TYPE_HEARTBEAT:self._onPktHeartbeat,
            TTPacketTypes.TYPE_DATA:self._onPktData,
        }
        self.isClosed = False
        self.callListener = False

    def close(self):
        self.conn.close()
    
    def bindUser(self, userId):
        assert(userId > 0)
        ttlog.info('Session bind user',
                   'sessionId=', self.sessionId,
                   'userId=', userId)
        self.userId = userId
        if self.server.app.sessionListener:
            self.server.app.sessionListener.onSessionBindUser(self)

    def cancelHeartbeatTimer(self):
        ttlog.info('Session cancel heartbeat',
                   'sessionId=', self.sessionId,
                   'userId=', self.userId)
        if self.heartbeatTimer:
            self.heartbeatTimer.cancel()

    def open(self):
        ttlog.info('Session open',
                   'sessionId=', self.sessionId,
                   'needServerHeartbeat=', self.conn.factory.needServerHeartbeat)
        if self.conn.factory.needServerHeartbeat:
            self.heartbeatTimer = TTTaskletTimer.runForever(6, self._doServerHeartbeat)
        if self.server.app.sessionListener:
            self.server.app.sessionListener.onSessionOpened(self)

    def onConnectionDataReceived(self, data):
        self.lastHeartbeatTime = time.time()
        for (pktType, pkt) in self.conn.factory.packetCodec.decode(data):
            if ttlog.isDebugEnabled():
                ttlog.debug('Session received packet',
                            'sessionId=', self.sessionId,
                            'userId=', self.userId,
                            'pktType=', pktType,
                            'pktLen=', len(pkt))
    
            handler = self._pktHandlerMap.get(pktType)
            if handler:
                handler(pktType, pkt)
            else:
                ttlog.info('Session received unknown packet',
                           'sessionId=', self.sessionId,
                           'userId=', self.userId,
                           'pktType=', pktType,
                           'pkgLen=', len(pkt))

    def onConnectionLost(self, reason):
        ttlog.info('Session connection lost',
                   'sessionId=', self.sessionId,
                   'userId=', self.userId,
                   'reason=', reason,
                   'callListener=', self.callListener)
        self.isClosed = True
        if self.heartbeatTimer:
            self.heartbeatTimer.cancel()
        if not self.callListener:
            self.callListener = True
            self.server.app.sessionListener.onSessionClosed(self, ConnLostReason.CONN_LOST)
    
    def sendMessage(self, msg):
        assert(isinstance(msg, TTMessage))
        self.sendPacket(TTPacketTypes.TYPE_DATA, self.conn.factory.messageCodec.encode(msg))
    
    def sendPacket(self, pktType, pkt):
        self.conn.send(self.conn.factory.packetCodec.encode(pktType, pkt))

    def sendRaw(self, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('Session.sendRaw',
                        'sessionId=', self.sessionId,
                        'userId=', self.userId,
                        'dataLen=', len(data),
                        'dataBufLen=', len(self.conn.transport.dataBuffer) - self.conn.transport.offset,
                        'tempDataLen=', self.conn.transport._tempDataLen)
        self.conn.sendRaw(data)

    def canSend(self, data):
        bufLen = len(self.conn.transport.dataBuffer) - self.conn.transport.offset
        if hasattr(self.conn.transport, '_tempDataLen'):
            bufLen += self.conn.transport._tempDataLen
        if bufLen > self.MAX_SEND_BUFFER:
            ttlog.warn('Session CannotSend',
                       'sessionId=', self.sessionId,
                       'userId=', self.userId,
                       'dataLen=', len(data),
                       'dataBufLen=', len(self.conn.transport.dataBuffer) - self.conn.transport.offset,
                       'tempDataLen=', self.conn.transport._tempDataLen,
                       'maxSendBuf=', self.MAX_SEND_BUFFER)
        return bufLen <= self.MAX_SEND_BUFFER
    
    def onHeartbeat(self, pkg):
        self.lastHeartbeatTime = time.time()
        ttlog.info('Session onHeartbeat',
                   'sessionId=', self.sessionId,
                   'userId=', self.userId,
                   'pkgLen=', len(pkg) if pkg else 0,
                   'isClosed=', self.isClosed)
        if (not self.isClosed
            and self.server.app.sessionListener):
            self.server.app.sessionListener.onSessionHeartbeat(self, pkg)
        
    def _onPktHeartbeat(self, pktType, pkt):
        self.onHeartbeat(pkt)

    def _onPktData(self, pktType, pkt):
        msg = self.conn.factory.messageCodec.decode(pkt)
        if ttlog.isDebugEnabled():
            ttlog.debug('Session received data',
                        'sessionId=', self.sessionId,
                        'userId=', self.userId,
                        'msg=', msg)
        try:
            self.server.handleMessage(self, msg)
        except:
            ttlog.error('TTSession._onPktData',
                        'sessionId=', self.sessionId,
                        'userId=', self.userId,
                        'msg=', msg)
    
    def _doServerHeartbeat(self):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSession._doServerHeartbeat',
                        'sessionId=', self.sessionId,
                        'userId=', self.userId)
        self.conn.factory.doServerHeartbeat(self.conn)


