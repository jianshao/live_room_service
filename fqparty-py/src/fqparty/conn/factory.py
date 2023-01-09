# -*- coding:utf-8 -*-
'''
Created on 2020年11月5日

@author: zhaojiangang
'''
from tomato.conn.composer import TTComposerFake
from tomato.conn.factory import TTSocketServerFactoryFactory, \
    TTWebSocketServerFactory, TTSocketServerFactoryFactoryDefault
from tomato.conn.message import TTPacketCodecFake, TTMessageCodec, TTMessage
from tomato.utils import ttlog, strutil
from tomato.utils.txws import WebSocketProtocol
from fqparty.const import MsgRoutes


class MessageCodecOld(TTMessageCodec):
    def encode(self, msg):
        return msg
    
    def decode(self, data):
        '''
        @return: TTMessage
        '''
        body = strutil.jsonLoads(data)
        msgId = body.get('msgId')
        if msgId == 1:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/bindAndEnterRoom', body)
        elif msgId == 73:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/heartbeat', body)
        elif msgId == 1002:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_USER_LEAVE, body)
        elif msgId == 2001:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_PK_START, body)
        elif msgId == 2002:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_PK_END, body)
        elif msgId == 2003:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_PK_ADD_COUNTDOWN, body)
        elif msgId == 2004:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/joinPKLocation', body)
        elif msgId == 2005:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/leavePKLocation', body)
        elif msgId == 2006:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/invitePKLocation', body)
        elif msgId == 2007:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/lockPKLocation', body)
        elif msgId == 2008:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/disablePKLocation', body)
        elif msgId == 2010:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, '/user/countdownPKLocation', body)
        elif msgId == 3001:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_CREATE_ACORSS_PK, body)
        elif msgId == 3002:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_ACORSS_PK_LIST, body)
        elif msgId == 3003:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_SPONSORE_ACORSS_PK, body)
        elif msgId == 3004:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_REPLY_ACORSS_PK, body)
        elif msgId == 3005:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_INVITE_PK_LIST, body)
        elif msgId == 3008:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_ACORSS_PKING_INFO, body)
        elif msgId == 3009:
            return TTMessage(TTMessage.TYPE_NOTIFY, 1, MsgRoutes.ROOM_SEARCH_ROOM, body)

class SocketServerFactoryFQ(TTWebSocketServerFactory):
    def __init__(self, server, packetCodec, messageCodec):
        TTWebSocketServerFactory.__init__(self, server, packetCodec, messageCodec)
        self.needServerHeartbeat = True

    def doServerHeartbeat(self, conn):
        if ttlog.isDebugEnabled():
            ttlog.debug('SocketServerFactoryFQ.doServerHeartbeat',
                        'peer=', conn.getPeer(),
                        'clientIp=', conn.getClientIp(),
                        'writePing')
        
        conn.writePing('1')


class WebSocketProtocolFQ(WebSocketProtocol):
    def __init__(self):
        WebSocketProtocol.__init__(self)
        self.do_binary_frames = False


class SocketServerFactoryFactoryFQ(TTSocketServerFactoryFactory):
    def __init__(self):
        self.defaultFactory = TTSocketServerFactoryFactoryDefault()
        
    def newSocketServerFactory(self, server, proto, conf):
        if proto == 'wsold':
            ttlog.info('SocketServerFactoryFactoryFQ.newSocketServerFactory',
                       'proto=', proto,
                       'conf=', conf)
            factory = SocketServerFactoryFQ(server, TTPacketCodecFake(), MessageCodecOld())
            factory.composer = TTComposerFake
            factory.protocol = WebSocketProtocolFQ
            ttlog.info('TTSocketServerFactoryFactoryFQ',
                       'composer=', factory.composer)
            return factory
        return self.defaultFactory.newSocketServerFactory(server, proto, conf)


