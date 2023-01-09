# -*- coding:utf-8 -*-
'''
Created on 2017年11月9日

@author: zhaojiangang
'''
import time

import msgpack

from tomato.agent.base import TTAgent
from tomato.db.redis import client
from tomato.utils import ttlog


class TTAgentSenderRedisPub(TTAgent.Sender):
    def __init__(self, agent, conf):
        self.agent = agent
        self.conf = conf
        self.conn = None
        
    def open(self):
        '''
        打开
        '''
        if not self.conn:
            self.conn = client.connectRedis(self.conf['host'], self.conf['port'], self.conf['db'], self.conf.get('password'), self.conf.get('timeout', 3))
            ttlog.info('Open sender %s %s' % (self.agent.serverId, self.conf))
            
    def close(self):
        '''
        关闭
        '''
        if self.conn:
            self.conn.stopTrying()
            if self.conn._client:
                self.conn._client.transport.loseConnection()
            self.conn = None
            
            ttlog.info('Close sender %s %s' % (self.agent.serverId, self.conf))
    
    def sendTo(self, targetId, data):
        '''
        发送data到targetId
        '''
        ts = time.time()
        
        if ttlog.isDebugEnabled():
            ttlog.debug('Message sending',
                        'sourceId=', self.agent.serverId,
                        'targetId=', targetId,
                        'ts=', ts,
                        'data=', type(data),
                        'len=', len(data),
                        'conn=', self.conn._client)

        msg = msgpack.packb([self.agent.serverId, targetId, data])
        self.conn.send('publish', 'req:%s' % (targetId), msg)
        
        if ttlog.isDebugEnabled():
            ttlog.debug('Message sent',
                        'sourceId=', self.agent.serverId,
                        'targetId=', targetId,
                        'ts=', ts,
                        'data=', type(data),
                        'len=', len(msg))


class TTAgentReceiverRedisSub(TTAgent.Receiver):
    def __init__(self, agent, conf):
        self.agent = agent
        self.conf = conf
        self.conn = None
        
    def open(self):
        '''
        开始接收
        '''
        if not self.conn:
            self.conn = client.connectSubscriber(self.conf['host'], self.conf['port'], self.conf['db'], self.conf.get('password'), self.conf.get('timeout', 3))
            ttlog.info('Open receiver %s %s' % (self.agent.serverId, self.conf))
    
    def close(self):
        '''
        关闭
        '''
        if self.conn:
            self.conn.stopTrying()
            if self.conn._client:
                self.conn._client.transport.loseConnection()
            self.conn = None
            
            ttlog.info('Close receiver %s %s' % (self.agent.serverId, self.conf))

    def startReceive(self, serverId):
        '''
        开始接收serverId的消息
        '''
        self.conn.subscribe('req:%s' % (serverId), self._onMessage)
        ttlog.info('Receiving',
                   'serverId=', serverId)
    
    def _onMessage(self, channel, msg):
        sourceId, targetId, data = msgpack.unpackb(msg)
        if ttlog.isDebugEnabled():
            ttlog.debug('Message received',
                        'sourceId=', sourceId,
                        'targetId=', targetId,
                        'len=', len(data))
        self.agent.onMessageReceived(sourceId, data)


class TTAgentTransportFactoryRedisPubsub(TTAgent.TransFactory):
    def newSender(self, agent, agentConf):
        return TTAgentSenderRedisPub(agent, agentConf) 

    def newReceiver(self, agent, agentConf):
        return TTAgentReceiverRedisSub(agent, agentConf)


