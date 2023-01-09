# -*- coding=utf-8 -*-
'''
Created on 2016年12月21日

@author: zjgzzz@126.com
'''
from twisted.internet.protocol import ReconnectingClientFactory, ClientFactory
from twisted.python.failure import Failure

from tomato.conn.composer import TTComposerInt32String
from tomato.conn.exceptions import TTConnException
from tomato.conn.message import TTMessage, TTPacketTypes
from tomato.conn.protocol import TTSocketProtocol
from tomato.core.exceptions import TTTimeoutException
from tomato.core.future import TTFuture
from tomato.core.tasklet import TTTasklet
from tomato.core.timer import TTTimer
from tomato.utils import ttlog


class TTConnectionHandler(object):
    def onConnectionOpen(self, conn):
        pass
    
    def onConnectionFailed(self, conn):
        pass
    
    def onConnectionClose(self, conn):
        pass
    
    def onConnectionMessage(self, conn, route, body):
        pass


class TTConnection(ClientFactory):
    protocol = TTSocketProtocol
    composer = TTComposerInt32String
    
    def __init__(self, packetCodec, messageCodec, heartbeatInterval, handler):
        self._curId = 0
        self._timeout = 19
        self._pendings = []
        self._waitingMap = {}
        self._packetCodec = packetCodec
        self._messageCodec = messageCodec
        self._conn = None
        self._heartbeatTimer = TTTimer.forever(heartbeatInterval, self._sendHeartbeat)
        self.handler = handler

    def close(self):
        ttlog.info('TTConnection.close')
        self._heartbeatTimer.cancel()
        if self._conn:
            self._conn.close()
    
    def sendRequest(self, route, msg):
        assert(self._conn)
        future = TTFuture()
        self._send(future, TTMessage.TYPE_REQUEST, route, msg)
        return future
        
    def sendNotify(self, route, msg):
        assert(self._conn)
        self._send(None, TTMessage.TYPE_NOTIFY, route, msg)

    def onConnectionOpen(self, conn):
        ttlog.info('TTConnection.onConnectionOpen',
                   'peer=', conn.getPeer(),
                   'clientIp=', conn.getClientIp())
        conn.pauseProducing()
        TTTasklet.createTasklet(self._onConnectionOpen, conn)
    
    def _onConnectionOpen(self, conn):
        ttlog.info('TTConnection._onConnectionOpen',
                   'peer=', conn.getPeer(),
                   'clientIp=', conn.getClientIp())
        conn.resumeProducing()
        self._conn = conn
        self._flushPendings()
        self._heartbeatTimer.start()
        if self.handler:
            self.handler.onConnectionOpen(self)
        
    def onConnectionDataReceived(self, conn, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnection.onConnectionDataReceived',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp(),
                        'len=', len(data))
        TTTasklet.createTasklet(self._onConnectionDataReceived, conn, data)
        
    def _handlePacket(self, pktType, pkt):
        if pktType == TTPacketTypes.TYPE_DATA:
            msg = self._messageCodec.decode(pkt)
            try:
                if ttlog.isDebugEnabled():
                    ttlog.debug('TTConnection._handlePacket',
                                'pktType=', pktType,
                                'msgId=', msg.msgId)
                if msg.msgType == TTMessage.TYPE_RESPONSE:
                    future, timer = self._waitingMap.pop(msg.msgId)
                    timer.cancel()
                    future.set(msg.body)
                elif msg.msgType == TTMessage.TYPE_PUSH:
                    if ttlog.isDebugEnabled():
                        ttlog.debug('TTConnection._handlePacket',
                                    'pktType=', pktType,
                                    'msgType=', 'PUSH',
                                    'msgId=', msg.msgId,
                                    'body=', msg.body)
                    if self.handler:
                        self.handler.onConnectionMessage(self, msg.route, msg.body)
            except KeyError:
                ttlog.warn('TTConnection._handlePacket',
                           'NoReuest msgId=', msg.msgId)
    
    def _onConnectionDataReceived(self, conn, data):
        '''
        transport收到一个数据包时回调
        '''
        for (pktType, pkt) in self._packetCodec.decode(data):
            self._handlePacket(pktType, pkt)
    
    def onConnectionLost(self, conn, reason):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnection.onConnectionLost',
                        'peer=', conn.getPeer(),
                        'reason=', reason)
        TTTasklet.createTasklet(self._onConnectionLost, conn, reason)

    def _onConnectionLost(self, conn, reason):
        self._conn = None
        self._heartbeatTimer.cancel()
        self._failedPendings(reason)
        if self.handler:
            self.handler.onConnectionClose(self)
    
    def clientConnectionFailed(self, connector, reason):
        self._failedPendings(reason)
        if self.handler:
            self.handler.onConnectionFailed(self)
        
    def _send(self, feture, msgType, route, msg):
        self._pendings.append((feture, msgType, route, msg))
        if self._conn:
            self._flushPendings()

    def _nextId(self):
        self._curId += 1
        return self._curId
    
    def _onReqTimeout(self, msgId):
        try:
            future, timer = self._waitingMap.pop(msgId)
            if timer:
                timer.cancel()
            if future:
                future.setFailure(Failure(TTTimeoutException('Time out for request: %s' % (msgId))))
        except:
            ttlog.warn('TTConnection._onReqTimeout',
                       'msgId=', msgId,
                       'err=', 'NotFoundRequest')

    def _failedPendings(self, reason):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnection._failedPendings',
                        'reason=', reason)
        pendings, self._pendings = self._pendings, []
        if pendings:
            failure = Failure(TTConnException(reason))
            for future, msgType, route, msg in pendings:
                ttlog.warn('TTConnection._failedPendings',
                           'msgType=', msgType,
                           'route=', route,
                           'msg=', msg)
                if future:
                    future.setFailure(failure)

    def _flushPendings(self):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnection._flushPendings')
        pendings, self._pendings = self._pendings, []
        for future, msgType, route, msg in pendings:
            msgId = self._nextId()
            pkg = self._messageCodec.encode(TTMessage(msgType, msgId, route, msg))
            self._sendPkt(TTPacketTypes.TYPE_DATA, pkg)
            if future:
                timer = TTTimer.once(self._timeout, self._onReqTimeout, msgId)
                self._waitingMap[msgId] = (future, timer)
                timer.start()
    
    def _sendPkt(self, pktType, pkt):
        self._conn.send(self._packetCodec.encode(pktType, pkt))
    
    def _sendHeartbeat(self):
        self._sendPkt(TTPacketTypes.TYPE_HEARTBEAT, None)


class TTConnectionClient(ReconnectingClientFactory):
    protocol = TTSocketProtocol
    composer = TTComposerInt32String
    
    def __init__(self, packetCodec, messageCodec, heartbeatInterval, msgHandler=None):
        self._curId = 0
        self._timeout = 19
        self._pendings = []
        self._waitingMap = {}
        self._packetCodec = packetCodec
        self._messageCodec = messageCodec
        self._conn = None
        self._heartbeatTimer = TTTimer.forever(heartbeatInterval, self._sendHeartbeat)
        self.msgHandler = msgHandler

    def close(self):
        self._heartbeatTimer.cancel()
        self.stopTrying()
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def sendRequest(self, route, msg):
        future = TTFuture()
        self._send(future, TTMessage.TYPE_REQUEST, route, msg)
        return future
        
    def sendNotify(self, route, msg):
        self._send(None, TTMessage.TYPE_NOTIFY, route, msg)

    def onConnectionOpen(self, conn):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnectionClient.onConnectionOpen',
                        'self=', id(self),
                        'conn=', id(conn))
        self._conn = conn
        self._flushPendings()
        self._heartbeatTimer.start()
    
    def onConnectionDataReceived(self, conn, data):
        '''
        transport收到一个数据包时回调
        '''
        for (pktType, pkt) in self._packetCodec.decode(data):
            self._handlePacket(pktType, pkt)
    
    def _handlePacket(self, pktType, pkt):
        if pktType == TTPacketTypes.TYPE_DATA:
            msg = self._messageCodec.decode(pkt)
            try:
                if ttlog.isDebugEnabled():
                    ttlog.debug('TTConnectionClient._handlePacket',
                                'pktType=', pktType,
                                'self=', id(self),
                                'msgId=', msg.msgId)
                if msg.msgType == TTMessage.TYPE_RESPONSE:
                    future, timer = self._waitingMap.pop(msg.msgId)
                    timer.cancel()
                    future.set(msg.body)
                elif msg.msgType == TTMessage.TYPE_PUSH:
                    if ttlog.isDebugEnabled():
                        ttlog.debug('TTConnectionClient._handlePacket',
                                    'pktType=', pktType,
                                    'self=', id(self),
                                    'msgType=', 'PUSH',
                                    'msgId=', msg.msgId,
                                    'body=', msg.body)
                    if self.msgHandler:
                        self.msgHandler(msg.route, msg.body)
            except KeyError:
                ttlog.warn('TTConnectionClient._handlePacket',
                           'pktType=', pktType,
                           'self=', id(self),
                           'NoReuest msgId=', msg.msgId)
        
    def onConnectionLost(self, conn, reason):
        ttlog.info('TTConnectionClient.onConnectionLost',
                   'self=', id(self),
                   'conn=', id(conn),
                   'reason=', reason)
        self._conn = None
        self._heartbeatTimer.cancel()
    
    def clientConnectionFailed(self, connector, reason):
        self._failedPendings(reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        
    def _send(self, feture, msgType, route, msg):
        self._pendings.append((feture, msgType, route, msg))
        if self._conn:
            self._flushPendings()

    def _nextId(self):
        self._curId += 1
        return self._curId
    
    def _onReqTimeout(self, msgId):
        try:
            future, timer = self._waitingMap.pop(msgId)
            if timer:
                timer.cancel()
            if future:
                future.setFailure(Failure(TTTimeoutException('Time out for request: %s' % (msgId))))
        except:
            ttlog.warn('TTConnectionClient._onReqTimeout',
                       'self=', id(self),
                       'msgId=', msgId,
                       'err=', 'NotFoundRequest')

    def _failedPendings(self, reason):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnectionClient._failedPendings',
                        'self=', id(self),
                        'reason=', reason)
        pendings, self._pendings = self._pendings, []
        if pendings:
            failure = Failure(TTConnException(reason))
            for future, msgType, route, msg in pendings:
                ttlog.warn('TTConnectionClient._failedPendings',
                           'self=', id(self),
                           'msgType=', msgType,
                           'route=', route,
                           'msg=', msg)
                if future:
                    future.setFailure(failure)

    def _flushPendings(self):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTConnectionClient._flushPendings',
                        'self=', id(self))
        pendings, self._pendings = self._pendings, []
        for future, msgType, route, msg in pendings:
            msgId = self._nextId()
            pkg = self._messageCodec.encode(TTMessage(msgType, msgId, route, msg))
            self._sendPkt(TTPacketTypes.TYPE_DATA, pkg)
            if future:
                timer = TTTimer.once(self._timeout, self._onReqTimeout, msgId)
                self._waitingMap[msgId] = (future, timer)
                timer.start()
    
    def _sendPkt(self, pktType, pkt):
        self._conn.send(self._packetCodec.encode(pktType, pkt))
    
    def _sendHeartbeat(self):
        self._sendPkt(TTPacketTypes.TYPE_HEARTBEAT, None)


