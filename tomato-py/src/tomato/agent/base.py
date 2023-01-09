# -*- coding:utf-8 -*-
'''
Created on 2017年11月8日

@author: zhaojiangang
'''

import time

from tomato.core.exceptions import TTException
from tomato.core.tasklet import TTTasklet
from tomato.utils import ttlog, strutil


class TTAgentMsgTypes(object):
    RPC = 1


class TTAgentDelegate(object):
    def handleAgentMessage(self, agent, sourceId, msgType, msg):
        '''
        处理消息
        '''
        raise NotImplementedError

    def routeByServerId(self, agent, serverId):
        '''
        查找serverId对应的agentId
        @retun: agentId
        '''
        raise NotImplementedError


class TTAgent(object):
    class Sender(object):
        def open(self):
            '''
            打开
            '''
            raise NotImplementedError
        
        def close(self):
            '''
            关闭
            '''
            raise NotImplementedError
        
        def sendTo(self, targetId, data):
            '''
            发送data到targetId
            '''
            raise NotImplementedError
    
    
    class Receiver(object):
        def open(self):
            '''
            开始接收
            '''
            raise NotImplementedError
        
        def close(self):
            '''
            关闭
            '''
            raise NotImplementedError
    
        def startReceive(self, channelId):
            '''
            开始接收channelId的消息
            '''
            raise NotImplementedError
        

    class TransFactory(object):
        def newReceiver(self, agent, agentInfo):
            raise NotImplementedError
        
        def newSender(self, agent, agentInfo):
            raise NotImplementedError

    
    def __init__(self, serverId, agentInfo, transFactory, delegate):
        self.serverId = serverId
        # map<agentId, Sender>
        self._senderMap = {}
        # Receiver
        self._receiver = None
        # agent配置信息
        self._agentInfo = agentInfo
        # trans工厂
        self._transFactory = transFactory
        # 代理
        self._delegate = delegate

    def isStart(self):
        return self._receiver != None
    
    def start(self):
        if not self._receiver:
            try:
                for _, sender in self._senderMap.iteritems():
                    sender.open()
                self._receiver = self._transFactory.newReceiver(self, self._agentInfo)
                self._receiver.open()
                self._receiver.startReceive(self.serverId)
            except:
                ttlog.error('TTAgent.start')
                self.stop()
                raise
    
    def stop(self):
        if self._receiver:
            self._receiver.close()
            self._receiver = None
        for _, sender in self._senderMap.iteritems():
            sender.close()
    
    def addAgent(self, agentId, agentInfo):
        '''
        添加agent
        '''
        assert(not self._findSender(agentId))
        sender = self._transFactory.newSender(self, agentInfo)
        self._senderMap[agentId] = sender
        
        ttlog.info('AddAgent', agentInfo)
        
    def removeAgent(self, agentId):
        '''
        删除agent
        '''
        sender = self._senderMap.pop(agentId)
        if sender:
            sender.close()
            ttlog.info('RemoveAgent', agentId)

    def sendTo(self, targetId, msgType, msg):
        '''
        发送msg到serverId
        '''
        if not self.isStart():
            raise TTException(-1, 'Agent not startted')
        
        if targetId == self.serverId:
            raise TTException(-1, 'Cannot send to self')

        # 根据targetId查找agentId
        agentId = self._delegate.routeByServerId(self, targetId)
        if not agentId:
            raise TTException(-1, 'Not found agent %s for serverId %s' % (agentId, targetId))

        sender = self._findSender(agentId)
        if not sender:
            raise TTException(-1, 'Not found agent %s' % (agentId))
    
        ts = time.time()
        data = strutil.msgpackDumps([ts, msgType, msg])
        sender.sendTo(targetId, data)
    
    def onMessageReceived(self, sourceId, data):
        '''
        有消息收到了，处理
        '''
        ts, msgType, msg = strutil.msgpackLoads(data)
        if ttlog.isDebugEnabled():
            ttlog.debug('TTAgent.onMessageReceived',
                        'sourceId=', sourceId,
                        'ts=', ts,
                        'msgType=', msgType,
                        'msgLen=', len(msg))
        TTTasklet.createTasklet(self._handleMessage, sourceId, msgType, msg)
        
    def _findSender(self, agentId):
        return self._senderMap.get(agentId)

    def _handleMessage(self, sourceId, msgType, msg):
        self._delegate.handleAgentMessage(self, sourceId, msgType, msg)


