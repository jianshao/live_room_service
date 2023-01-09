# -*- coding:utf-8 -*-
'''
Created on 2017年4月11日

@author: zhaojiangang
'''
from contextlib import contextmanager
from functools import wraps
import stackless

from tomato.utils import ttlog
from fqparty.utils import time_utils


class TTLock(object):
    def __init__(self):
        super(TTLock, self).__init__()
        self._channel = stackless.channel()
        self._islock = False
        self._tasklet = None
        self._relock = 0

    @property
    def isLocked(self):
        return self._islock

    def lock(self):
        if self._islock == True:
            if self._tasklet == stackless.getcurrent() :
                self._relock += 1
                return
            self._channel.receive()
        self._islock = True
        self._tasklet = stackless.getcurrent()

    def unlock(self):
        if self._relock > 0:
            self._relock -= 1
            return 1
        self._tasklet = None
        self._islock = False
        if self._channel.balance < 0 :
            self._channel.send(0)
            return 1
        return 0


class TTKeyLock(object):
    def __init__(self):
        # key=key, value=TTLock()
        self._lockMap = {}

    @contextmanager
    def lock(self, key):
        startTime = time_utils.getCurrentTimestampFloat()
        locker = self._findOrCreateLocker(key)
        locker.lock()
        try:
            if ttlog.isDebugEnabled():
                ttlog.debug('TTKeyLock.locked key=', key, type(key), id(locker))
            yield
        except:
            raise
        finally:
            locker.unlock()
            if not locker.isLocked:
                try:
                    del self._lockMap[key]
                except:
                    pass

            endTime = time_utils.getCurrentTimestampFloat()
            if endTime - startTime >= 1:
                ttlog.info('TTKeyLock.ulocked key=', key, type(key), id(locker),
                           'endTime=', endTime,
                           'startTime=', startTime,
                           'diff=', endTime - startTime)

    def _findOrCreateLocker(self, key):
        locker = self._lockMap.get(key)
        if not locker:
            locker = TTLock()
            self._lockMap[key] = locker
        return locker


@contextmanager
def lock(locker):
    '''e.g.
        with lock(lockable.locker) :
            ...
    '''
    locker.lock()
    try:
        if ttlog.isDebugEnabled():
            ttlog.debug('locker %s locked' % (locker))
        yield
    except:
        raise
    finally:
        if ttlog.isDebugEnabled():
            ttlog.debug('locker %s unlock' % (locker))
        locker.unlock()


def locked(func):
    '''
        class Lockable(object) : 
            def __init__(self):
                self.locker = TTLock()

            @locked
            def lockedMethod(self):
                pass
    '''
    @wraps(func)
    def syncfunc(*args, **kw):
        objself = args[0] 
        if not hasattr(objself, 'locker') :
            objself.locker = TTLock()

        with lock(objself.locker) :
            if ttlog.isDebugEnabled():
                ttlog.debug('locked func:', func.__name__)
            return func(*args, **kw)

    return syncfunc


