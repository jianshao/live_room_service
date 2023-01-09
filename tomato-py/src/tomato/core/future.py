# -*- coding=utf-8 -*-
'''
Created on 2016年5月11日

@author: zjgzzz
'''
from stackless import bomb
import stackless

from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from tomato.core import reactor
from tomato.core.exceptions import TTTimeoutException


class TTFuture(object):
    def __init__(self, deferred=None):
        self._result = None
        self._deferred = deferred or Deferred()
        self._deferred.addCallback(self._success).addErrback(self._error)

    def get(self, timeout=None):
        if self._result:
            if 'result' in self._result:
                return self._result['result']
            excInfo = self._result['excInfo']
            raise excInfo[0], excInfo[1], excInfo[2]
        
        channel = stackless.channel()
        def _callback(_):
            if channel.balance != 0:
                if 'result' in self._result:
                    channel.send(self._result['result'])
                else:
                    excInfo = self._result['excInfo']
                    channel.send(bomb(excInfo[0], excInfo[1], excInfo[2]))

        def _timeout():
            if channel.balance != 0:
                channel.send(bomb(TTTimeoutException, TTTimeoutException('Get response timeout'), None))

        if timeout is not None:
            t = reactor.callLater(timeout, _timeout)
            self._deferred.addBoth(lambda r: t.cancel())

        self._deferred.addBoth(_callback)
        return channel.receive()
    
    def set(self, value):
        self._deferred.callback(value)
    
    def setException(self, excInfo=None):
        if excInfo:
            failure = Failure(excInfo[1], excInfo[0], excInfo[2])
        else:
            failure = Failure()
        self.setFailure(failure)
    
    def setFailure(self, failure):
        assert(isinstance(failure, Failure))
        self._deferred.errback(failure)
        
    def _success(self, result):
        self._result = {'result':result}
        return result
    
    def _error(self, failure):
        self._result = {'excInfo':(failure.type, failure.value, failure.tb)}
        return failure


