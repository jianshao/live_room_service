# -*- coding=utf-8 -*-
'''
Created on 2016年4月20日

@author: zjgzzz@126.com
'''

import stackless

from twisted.internet import reactor

from tomato.utils import ttlog


_reactor = reactor

def _scheduleIfNeed():
    rc = stackless.getruncount()
    if rc > 1:
        stackless.schedule()

def stop():
    try:
        _reactor.callLater(0, _reactor.stop)
        ttlog.info('Notify main loop stop' )
    except:
        pass

def isRunning():
    return _reactor._started

def callWhenRunning(callable_, *args, **kw):
    return _reactor.callWhenRunning(callable_, *args, **kw)

def callLater(delay, callable_, *args, **kw):
    return _reactor.callLater(delay, callable_, *args, **kw)

def listenTCP(port, factory, backlog=50, interface=''):
    return _reactor.listenTCP(port, factory, backlog, interface)

def connectTCP(host, port, factory, timeout=30, bindAddress=None):
    return _reactor.connectTCP(host, port, factory, timeout, bindAddress)
        
def connectSSL(host, port, factory, contextFactory, timeout=30, bindAddress=None):
    return _reactor.connectSSL(host, port, factory, contextFactory, timeout, bindAddress)

def listenSSL(port, factory, contextFactory, backlog=50, interface=''):
    return _reactor.listenSSL(port, factory, contextFactory, backlog, interface)
    
def run():
    _reactor.startRunning()
    while _reactor._started:
        try:
            while _reactor._started:
                # Advance simulation time in delayed event
                # processors.
                _reactor.runUntilCurrent()
                _scheduleIfNeed()
                t2 = _reactor.timeout()
                t = _reactor.running and t2
                _reactor.doIteration(t)
                _scheduleIfNeed()
        except:
            ttlog.error('Unexpected error in main loop.')
        else:
            ttlog.info('Main loop terminated.')
        finally:
            _scheduleIfNeed()


