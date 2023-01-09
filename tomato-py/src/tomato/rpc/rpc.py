# -*- coding:utf-8 -*-
'''
Created on 2017年11月9日

@author: zhaojiangang
'''
import struct

from twisted.internet import defer
from twisted.python.failure import Failure

from tomato.agent.base import TTAgentMsgTypes
from tomato.core.exceptions import TTTimeoutException, TTException
from tomato.core.future import TTFuture
from tomato.core.timer import TTTaskletTimer
from tomato.rpc.exceptions import TTRPCRemoteException
from tomato.utils import ttlog, strutil


MAX_MSG_ID = 0x7fffffff
MSG_TYPE_REQ = 1
MSG_TYPE_RESP = 2


def encodeRequest(answerRequired, reqId, service, method, args):
    msg = strutil.msgpackDumps([answerRequired, reqId, service, method, args])
    return struct.pack('!B', MSG_TYPE_REQ) + msg


def decodeRequest(data):
    return strutil.msgpackLoads(data)


def encodeResponse(reqId, ec, resp):
    msg = strutil.msgpackDumps([reqId, ec, resp])
    return struct.pack('!B', MSG_TYPE_RESP) + msg


def decodeResponse(data):
    return strutil.msgpackLoads(data)


def decodeMsg(data):
    msgType, = struct.unpack('!B', data[0])
    return msgType, data[1:]


class TTRPC(object):
    def __init__(self, agent, rootService):
        self._curId = 0
        self._reqMap = {}
        self._agent = agent
        self._rootService = rootService

    def call(self, targetId, service, method, *args, **kw):
        '''
        调用远程方法
        @param targetId: 目标服务器ID
        @param service: 要调用的服务名称
        @param method: 要调用的服务中的方法
        @param args: 参数
        @param kw: 目前支持timeout表示超时时间，如果不设置用默认的, block=1表示阻塞，默认=1
        @return: 如果block=1则返回回应，否则返回TTFuture对象
        '''
        reqId = self._nextReqId()
        data = encodeRequest(True, reqId, service, method, args)
        if ttlog.isDebugEnabled():
            ttlog.debug('TTRPC.call',
                        'reqId=', reqId,
                        'targetId=', targetId,
                        'service=', service,
                        'method=', method,
                        'args=', args)

        timeout = kw.get('timeout', 6)
        timer = TTTaskletTimer.once(timeout, self._onRequestTimeout, reqId, service, method, args)
        d = defer.Deferred()
        self._reqMap[reqId] = (d, timer)
        timer.start()
        
        self._agent.sendTo(targetId, TTAgentMsgTypes.RPC, data)
        
        future = TTFuture(d)
        if kw.get('block', 1) == 1:
            return future.get()
        return future

    def post(self, targetId, service, method, *args):
        '''
        调用远程方法，不需要回应
        @param targetId: 目标服务器ID
        @param service: 要调用的服务名称
        @param method: 要调用的服务中的方法
        @param args: 参数
        '''
        reqId = self._nextReqId()
        if ttlog.isDebugEnabled():
            ttlog.debug('TTRPC.post',
                        'reqId=', reqId,
                        'targetId=', targetId,
                        'service=', service,
                        'method=', method,
                        'args=', args)

        data = encodeRequest(False, reqId, service, method, args)
        self._agent.sendTo(targetId, TTAgentMsgTypes.RPC, data)
    
    def handleRpcMessage(self, agent, sourceId, msg):
        if ttlog.isTraceEnabled():
            ttlog.trace('>>> handleRpcMessage',
                        'sourceId=', sourceId,
                        'len=', len(msg))
        try:
            msgType, rpcMsg = decodeMsg(msg)
            if msgType == MSG_TYPE_REQ:
                answerRequired, reqId, service, method, args = decodeRequest(rpcMsg)
                self._handleRequest(sourceId, answerRequired, reqId, service, method, args)
            elif msgType == MSG_TYPE_RESP:
                reqId, ec, resp = decodeResponse(rpcMsg)
                self._handleResponse(sourceId, reqId, ec, resp)
        except:
            ttlog.error('Error handle message',
                        'sourceId=', sourceId,
                        'len=', len(msg))
    
    def _nextReqId(self):
        self._curId += 1
        if self._curId > MAX_MSG_ID:
            self._curId = 1
        return self._curId
    
    def _onRequestTimeout(self, reqId, service, method, args):
        if ttlog.isDebugEnabled():
            ttlog.debug('TTRPC._onRequestTimeout',
                   'reqId=', reqId,
                   'service=', service,
                   'method=', method,
                   'args=', args)
        try:
            deferred, timer = self._reqMap.pop(reqId)
            if timer:
                timer.cancel()
            if deferred:
                deferred.errback(Failure(TTTimeoutException('Time out for request: %s' % (reqId))))
        except KeyError:
            ttlog.warn('Not found request for timeout',
                       'reqId=', reqId,
                       'service=', service,
                       'method=', method,
                       'args=', args)

    def _handleRequest(self, sourceId, answerRequired, reqId, service, method, args):
        if ttlog.isDebugEnabled():
            ttlog.debug('>>> TTRPC.handleRequest',
                        'sourceId=', sourceId,
                        'answerRequired=', answerRequired,
                        'reqId=', reqId,
                        'service=', service,
                        'method=', method,
                        'args=', args)

        try:
            ec, resp = 0, self._rootService.call(service, method, *args)
            if ttlog.isDebugEnabled():
                ttlog.debug('TTRPC.handleRequest',
                            'sourceId=', sourceId,
                            'answerRequired=', answerRequired,
                            'reqId=', reqId,
                            'service=', service,
                            'method=', method,
                            'args=', args,
                            'ec=', ec,
                            'resp=', resp)
        except TTException, e:
            ttlog.error('Error handle request',
                        'sourceId=', sourceId,
                        'answerRequired=', answerRequired,
                        'reqId=', reqId,
                        'service=', service,
                        'method=', method,
                        'args=', args)
            ec, resp = 1, [e.errorCode, e.message]
        except Exception, e:
            ttlog.error('Error handle request',
                        'sourceId=', sourceId,
                        'answerRequired=', answerRequired,
                        'reqId=', reqId,
                        'service=', service,
                        'method=', method,
                        'args=', args)
            ec, resp = 1, [-1, e.message]
            
        if answerRequired:
            if ttlog.isDebugEnabled():
                ttlog.debug('SendResponse',
                            'sourceId=', sourceId,
                            'reqId=', reqId,
                            'service=', service,
                            'method=', method,
                            'args=', args,
                            'ec=', ec,
                            'resp=', resp)
            self._agent.sendTo(sourceId, TTAgentMsgTypes.RPC, encodeResponse(reqId, ec, resp))

    def _handleResponse(self, sourceId, reqId, ec, resp):
        '''
        响应回调
        '''
        try:
            if ttlog.isDebugEnabled():
                ttlog.debug('TTRPC._handleResponse',
                            'sourceId=', sourceId,
                            'reqId=', reqId,
                            'ec=', ec,
                            'resp=', resp,
                            'reqMap=', self._reqMap.keys())
            deferred, timer = self._reqMap.pop(reqId)
            timer.cancel()
            if ec == 0:
                deferred.callback(resp)
            else:
                deferred.errback(TTRPCRemoteException(*resp))
        except KeyError:
            ttlog.warn('Not found request for resp',
                       'sourceId=', sourceId,
                       'reqId=', reqId,
                       'ec=', ec,
                       'resp=', resp)


