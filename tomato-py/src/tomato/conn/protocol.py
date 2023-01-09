# -*- coding=utf-8 -*-
'''
Created on 2017年11月22日

@author: zhaojiangang
'''
from twisted.internet import protocol
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import _PauseableMixin
import socket
from tomato.utils import ttlog


class TTSocketProtocol(protocol.Protocol, _PauseableMixin):
    composer = None
    userData = None
    
    def abort(self):
        if hasattr(self.transport, 'abortConnection'):
            self.transport.abortConnection()
        else:
            self.transport.loseConnection()
    
    def close(self):
        self.transport.loseConnection()
        
    def getPeer(self):
        return self.transport.getPeer()
    
    def getHost(self):
        return self.transport.getHost()

    def getClientIp(self):
        return self.getPeer().host
    
    def send(self, data):
        self.sendRaw(self.composer.compose(data))
    
    def sendRaw(self, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSocketProtocol.sendRaw',
                        'peer=', self.getPeer(),
                        'len=', len(data),
                        'dataBuffLen=', len(self.transport.dataBuffer),
                        'tempDataLen=', self.transport._tempDataLen)
        self.transport.write(data)
    
    def connectionMade(self):
        ttlog.info('TTSocketProtocol.connectionMade',
                   'peer=', self.getPeer())
        try:
            self.transport.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.composer = self.factory.composer()
            self.factory.onConnectionOpen(self)
        except:
            ttlog.error('TTSocketProtocol.connectionMade',
                        'peer=', self.getPeer())
            self.abort()

    def connectionLost(self, reason=connectionDone):
        ttlog.info('TTConnectionProtocol.connectionLost',
                   'peer=', self.transport.getPeer(),
                   'reason=', reason)
        try:
            self.factory.onConnectionLost(self, reason)
        except:
            ttlog.error('TTSocketProtocol.connectionLost',
                        'peer=', self.getPeer(),
                        'reason=', reason)
        
    def dataReceived(self, data):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTSocketProtocol.dataReceived',
                        'peer=', self.getPeer(),
                        'len=', len(data))
        try:
            for pkg in self.composer.feed(data):
                if not self.transport.disconnecting:
                    self.factory.onConnectionDataReceived(self, pkg)
        except:
            ttlog.error('TTSocketProtocol.dataReceived',
                        'peer=', self.getPeer(),
                        'len=', len(data))
            self.abort()


