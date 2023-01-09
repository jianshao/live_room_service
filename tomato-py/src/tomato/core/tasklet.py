# -*- coding=utf-8 -*-
'''
Created on 2016年10月21日

@author: zjgzzz@126.com
'''
import stackless
import sys

from twisted.internet.defer import Deferred

from tomato.core import reactor
from tomato.core.future import TTFuture
from tomato.core.exceptions import TTException
from tomato.utils import ttlog


class TTActorAlreadyDeadException(TTException):
    def __init__(self, message='Actor already dead'):
        super(TTActorAlreadyDeadException, self).__init__(-1, message)


class TTTasklet(object):
    def __init__(self, target, *args, **kw):
        assert(not target or callable(target))
        self._tasklet = stackless.tasklet(self._run)(*args, **kw)
        self._target = target
        self._tasklet._ttTasklet = self
        self.userData = {}
    
    @property
    def tasklet(self):
        return self._tasklet

    @classmethod
    def sleep(self, delay):
        def _timeout(ch):
            ch.send(None)
        d = Deferred()
        ch = stackless.channel()
        t = reactor.callLater(delay, _timeout, ch)
        d.addBoth(lambda r:t.cancel())
        return ch.receive()
    
    @classmethod
    def current(self):
        return stackless.getcurrent()._ttTasklet
    
    @classmethod
    def createTasklet(cls, func, *args, **kw):
        return TTTasklet(func, *args, **kw)
    
    @classmethod
    def taskletCount(cls):
        return stackless.getruncount()

    def _run(self, *args, **kw):
        if self._target:
            try:
                self._target(*args, **kw)
            except:
                ttlog.error('TTTasklet._run',
                            'target=', self._target,
                            'args=', args,
                            'kw=', kw)


class TTActor(TTTasklet):
    def __init__(self):
        super(TTActor, self).__init__()
        # 消息通道
        self._channel = stackless.channel()
        # 是否停止
        self._stopped = False
    
    def isAlive(self):
        return not self._stopped
    
    def stop(self):
        if not self.isAlive():
            raise TTActorAlreadyDeadException()
        self._sendCommand(None, {'command':'stop'})
    
    def tell(self, message):
        if not self.isAlive():
            raise TTActorAlreadyDeadException()
        self._sendCommand(None, {'command':'msg', 'msg':message})
    
    def ask(self, message, block=True, timeout=None):
        if not self.isAlive():
            raise TTActorAlreadyDeadException()
        future = TTFuture()
        self._sendCommand(future, {'command':'msg', 'msg':message})
        if block:
            return future.get(timeout)
        return future
    
    def _sendCommand(self, future, command):
        self._channel.send((future, command))
    
    def _run(self, *args, **kw):
        try:
            self._onStart()
        except:
            self._handleFailure(*sys.exc_info())
            
        while not self._stopped:
            future, message = self._channel.receive()
            try:
                self._handleReceived(future, message)
            except:
                if future:
                    future.setException(sys.exc_info())
                else:
                    self._handleFailure(*sys.exc_info())
                    try:
                        self._onFailure(*sys.exc_info())
                    except:
                        self._handleFailure(*sys.exc_info())
        
        while self._channel.balance > 0:
            future, message = self._channel.receive()
            if future:
                future.setException((TTActorAlreadyDeadException, TTActorAlreadyDeadException(), None))
            
    def _handleReceived(self, future, message):
        cmd = message.get('command')
        if cmd == 'stop':
            self._stop()
        elif cmd == 'msg':
            resp = self._onReceived(message.get('msg'))
            if future:
                future.set(resp)
        else:
            ttlog.error('Unknown command %s' % (cmd))
        
    def _handleFailure(self, exception_type, exception_value, traceback):
        ttlog.error('Unhandled exception in %s:' % self,
                    exc_info=(exception_type, exception_value, traceback))
        self._stopped = True
        
    def _stop(self):
        self._stopped = True
        try:
            self._onStop()
        except:
            self._handleFailure(*sys.exc_info())
        
    def _onStart(self):
        pass
    
    def _onStop(self):
        pass
    
    def _onFailure(self, exception_type, exception_value, traceback):
        pass
    
    def _onReceived(self, future, message):
        pass


