# -*- coding:utf-8 -*-
'''
Created on 2017年10月9日

@author: zhaojiangang
'''
import json
import struct

from tomato.conn.exceptions import TTProtocolException
from tomato.core.exceptions import TTException
from tomato.utils import ttlog


class TTPacketTypes(object):
    TYPE_HEARTBEAT = 1
    TYPE_DATA = 2


class TTPacketCodec(object):
    def encode(self, pktType, pkg):
        '''
        @return: data
        '''
        raise NotImplementedError
    
    def decode(self, data):
        '''
        解析package
        '''
        raise NotImplementedError


class TTPacketCodecDefault(TTPacketCodec):
    maxPacketLength = 1 << 24
    headLength = 4
    
    def encode(self, pktType, pkt):
        '''
        @return: data
        '''
        pktLen = len(pkt) if pkt else 0
        if pktLen > self.maxPacketLength:
            raise TTProtocolException("Packet too long")

        head = pktType << 24 | pktLen
        ret = b''
        ret += struct.pack('!I', head)
        if pkt:
            ret += pkt
        return ret
    
    def decode(self, data):
        '''
        解析packet
        @return: packetType, packet
        '''
        while data and len(data) >= self.headLength:
            head, = struct.unpack('!I', data[0:self.headLength])
            pktType = head >> 24
            pktLen = head & 0x00FFFFFF
            if ttlog.isDebugEnabled():
                ttlog.debug('TTPacketCodecDefault.decode',
                            'head=', head,
                            'pktType=', pktType,
                            'pktLen=', pktLen,
                            'dataLen=', len(data))
            if self.headLength + pktLen > len(data):
                return
            yield (pktType, data[self.headLength:self.headLength+pktLen])
            data = data[self.headLength + pktLen:]


class TTPacketCodecFake(TTPacketCodec):
    def encode(self, pktType, pkt):
        return pkt
    
    def decode(self, data):
        yield (TTPacketTypes.TYPE_DATA, data)


class TTMessage(object):
    TYPE_REQUEST = 1
    TYPE_NOTIFY = 2
    TYPE_RESPONSE = 3
    TYPE_PUSH = 4
    
    def __init__(self, msgType=None, msgId=None, route=None, body=None):
        self.msgType = msgType
        self.msgId = msgId
        self.route = route
        self.body = body

    def toDict(self):
        return {
            'msgType':self.msgType,
            'msgId':self.msgId,
            'route':self.route,
            'body':self.body
        }
    
    def fromDict(self, d):
        self.msgType = d['msgType']
        self.msgId = d['msgId']
        self.route = d['route']
        self.body = d['body']
        return self
    
    @property
    def needResponse(self):
        return self.msgType == self.TYPE_REQUEST

    @classmethod
    def isValidType(cls, msgType):
        return msgType >= cls.TYPE_REQUEST and msgType <= cls.TYPE_PUSH
    
    def makeResponse(self, resp):
        assert(self.msgType == self.TYPE_REQUEST)
        return TTMessage(self.TYPE_RESPONSE, self.msgId, None, resp)
    
    @classmethod
    def makePush(cls, route, body):
        return TTMessage(TTMessage.TYPE_PUSH, 0, route, body)
    

class TTSessionInfo(object):
    def __init__(self, frontId=None, sessionId=None, clientIp=None, userId=0):
        self.sessionId = sessionId
        self.frontId = frontId
        self.clientIp = clientIp
        self.userId = userId
    
    def toDict(self):
        return {
            'sessionId':self.sessionId,
            'frontId':self.frontId,
            'clientIp':self.clientIp,
            'userId':self.userId
        }
    
    def fromDict(self, d):
        self.sessionId = d['sessionId']
        self.frontId = d['frontId']
        self.clientIp = d['clientIp']
        self.userId = d['userId']
        return self
    
    def __str__(self):
        return '%s:%s:%s:%s' % (self.frontId, self.sessionId, self.clientIp, self.userId)
    
    def __unicode__(self):
        return u'%s:%s:%s:%s' % (self.frontId, self.sessionId, self.clientIp, self.userId)

    def __repr__(self):
        return str(self)


class TTMessageController(object):
    def __init__(self):
        self._handlerMap = {}

    def addHandler(self, route, handler):
        if route in self._handlerMap:
            raise TTException(-1, 'route already exists')
        self._handlerMap[route] = handler

    def handleMessage(self, msg, sessionInfo):
        handler = self._findHandler(msg.route)
        if handler:
            return handler(msg, sessionInfo)
        raise TTException(-1, 'Not found handler for %s %s' % (str(sessionInfo), msg.route))

    def _findHandler(self, route):
        handler = self._handlerMap.get(route)
        if handler:
            return handler
        
        index = route.rfind('/')
        
        if index > 0:
            r = route[0:index + 1]
            r += '*'
            return self._handlerMap.get(r)
        
        return None


class TTMessageCodec(object):
    def encode(self, msg):
        '''
        @return: data
        '''
        raise NotImplementedError
    
    def decode(self, data):
        '''
        @return: TTMessage
        '''
        raise NotImplementedError


class TTMessageCodecDefault(TTMessageCodec):
    HEAD_FMT = '!BIBI'
    HEAD_LEN = struct.calcsize(HEAD_FMT)
    
    def encode(self, msg):
        data = struct.pack(self.HEAD_FMT,
                           msg.msgType,
                           msg.msgId,
                           len(msg.route) if msg.route else 0,
                           len(msg.body) if msg.body else 0)
        if msg.route:
            data += msg.route
        if msg.body:
            data += msg.body
        return data
        
    def decode(self, data):
        if len(data) < self.HEAD_LEN:
            raise TTProtocolException('Too short data for HEAD_LEN')
        msgType, msgId, routeLen, msgLen = struct.unpack(self.HEAD_FMT, data[0:self.HEAD_LEN])
        if len(data) < self.HEAD_LEN + routeLen + msgLen:
            raise TTProtocolException('Too short data for LEN')
        if not TTMessage.isValidType(msgType):
            raise TTProtocolException('Bad message type')
        if routeLen > 255:
            raise TTProtocolException('Too lang routeLen')
        route = None
        if routeLen > 0:
            route = data[self.HEAD_LEN:self.HEAD_LEN + routeLen]
        msg = None
        if msgLen > 0:
            msg = data[self.HEAD_LEN + routeLen:self.HEAD_LEN + routeLen + msgLen]
        return TTMessage(msgType, msgId, route, msg)


class TTMessageCodecJson(TTMessageCodec):
    def __init__(self, codec=None):
        self._codec = codec or TTMessageCodecDefault()
        
    def encode(self, msg):
        if msg.body is not None:
            msg.body = json.dumps(msg.body, separators=(',', ':'))
        return self._codec.encode(msg)

    def decode(self, msg):
        msg = self._codec.decode(msg)
        if msg.body:
            msg.body = json.loads(msg.body)
        return msg


    