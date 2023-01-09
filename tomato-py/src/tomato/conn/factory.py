# -*- coding:utf-8 -*-
'''
Created on 2020年11月5日

@author: zhaojiangang
'''
from twisted.internet.protocol import ServerFactory

from tomato.conn.composer import TTComposerInt32String, TTComposerFake
from tomato.conn.message import TTPacketCodecDefault, TTMessageCodecJson,\
    TTPacketTypes
from tomato.conn.protocol import TTSocketProtocol
from tomato.utils import ttlog
from tomato.utils.txws import WebSocketProtocol
from tomato.core.tasklet import TTTasklet


class TTSocketServerFactory(ServerFactory):
    composer = TTComposerInt32String
    protocol = TTSocketProtocol
    needServerHeartbeat = False

    def __init__(self, server, packetCodec, messageCodec, needServerHeartbeat=False):
        self.server = server
        self.packetCodec = packetCodec
        self.messageCodec = messageCodec
        self.needServerHeartbeat = needServerHeartbeat

    @property
    def app(self):
        return self.server.app
    
    def onConnectionOpen(self, conn):
        ttlog.info('TTSocketServerFactory.onConnectionOpen',
                   'peer=', conn.getPeer(),
                   'clientIp=', conn.getClientIp())
        self.server.onConnectionOpen(conn)

    def onConnectionDataReceived(self, conn, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSocketServerFactory.onConnectionDataReceived',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp(),
                        'len=', len(data))
        self.server.onConnectionDataReceived(conn, data)

    def onConnectionLost(self, conn, reason):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSocketServerFactory.onConnectionLost',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp(),
                        'reason=', reason)
        self.server.onConnectionLost(conn, reason)
    
    def doServerHeartbeat(self, conn):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSocketServerFactory.doServerHeartbeat',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp())
        
        conn.sendPacket(TTPacketTypes.TYPE_HEARTBEAT, None)
    

class TTWebSocketServerFactory(TTSocketServerFactory):
    composer = TTComposerFake
    protocol = WebSocketProtocol
    
    def __init__(self, server, packetCodec, messageCodec, needServerHeartbeat=False):
        TTSocketServerFactory.__init__(self, server, packetCodec, messageCodec, needServerHeartbeat)

    def onConnectionPingReceived(self, conn, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTWebSocketServerFactory.onConnectionPingReceived',
                        'peer=', conn.getPeer(),
                        'userId=', conn.userData.userId if conn.userData else 0)
        
        session = conn.userData
        if session:
            TTTasklet.createTasklet(session.onHeartbeat, data)

    def onConnectionPongReceived(self, conn, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTWebSocketServerFactory.onConnectionPongReceived',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp(),
                        'userId=', conn.userData.userId if conn.userData else 0)
        session = conn.userData
        if session:
            TTTasklet.createTasklet(session.onHeartbeat, data)


class TTSocketServerFactoryFactory(object):
    def newSocketServerFactory(self, server, proto, conf):
        raise NotImplementedError


class TTSocketServerFactoryFactoryDefault(TTSocketServerFactoryFactory):
    def newSocketServerFactory(self, server, proto, conf):
        if proto == 'tcp':
            return TTSocketServerFactory(server, TTPacketCodecDefault(), TTMessageCodecJson())
        elif proto == 'ws':
            def protocolFactory():
                protocol = WebSocketProtocol()
                protocol.do_binary_frames = True
                return protocol
            factory = TTSocketServerFactory(server, TTPacketCodecDefault(), TTMessageCodecJson())
            factory.protocol = protocolFactory
            factory.composer = TTComposerFake
            return factory


