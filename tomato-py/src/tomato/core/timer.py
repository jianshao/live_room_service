# -*- coding=utf-8 -*-
'''
Created on 2016年2月28日

@author: zjgzzz@126.com
'''

from tomato.core import reactor
from tomato.utils import ttlog
from tomato.core.tasklet import TTTasklet


class TTTimer(object):
    def __init__(self, interval, repeatCount, handler, *args, **kw):
        '''
        @param interval: 定时器时间间隔，单位为秒，浮点型
        @param repeatCount: 重复执行次数, -1表示一直重复
        @param handler: 定时器触发时执行的方法
        @param args: handler执行时的参数
        @param kw: handler执行时的参数
        '''
        assert(repeatCount >= -1)
        self._interval = interval
        self._repeatCount = repeatCount
        self._curRepeatCount = 0
        self._handler = handler
        self._args = args
        self._kw = kw
        self._timer = None
        self._cancelled = False

    @property
    def repeatCount(self):
        return self._repeatCount
    
    @property
    def cancelled(self):
        return self._cancelled
    
    @property
    def interval(self):
        return self._interval
    
    def start(self):
        self.cancel()
        self._cancelled = False
        self._timer = reactor.callLater(self._interval, self._onTimeout)
        return self
    
    def resetInterval(self, interval):
        self._interval = interval
        if not self._cancelled and self._timer:
            if self._timer and not self._timer.cancelled and not self._timer.called:
                self._timer.reset(self._interval)
    
    def cancel(self):
        timer = self._timer
        self._timer = None
        self._cancelled = True
        if timer and not timer.cancelled and not timer.called:
            timer.cancel()

    def getExpiresTime(self):
        '''
        获取到期时间，如果没有启动或者已经cancel了就返回None
        '''
        if self._timer and not self._timer.cancelled and not self._timer.called:
            return self._timer.getTime()
        return None

    def _onTimeout(self):
        try:
            ttlog.debug('TTTimer._onTimeout',
                        'handler=', self._handler,
                        'cancelled=', self._cancelled,
                        'args=', self._args,
                        'kw=', self._kw)
            self._handler(*self._args, **self._kw)
        except:
            ttlog.error('TTTimer._onTimeout',
                        'handler=', self._handler,
                        'args=', self._args,
                        'kw=', self._kw)
        
        if (not self._cancelled
            and (self._repeatCount < 0 or self._curRepeatCount < self._repeatCount)):
            self._curRepeatCount += 1
            self._timer = reactor.callLater(self._interval, self._onTimeout)

    @classmethod
    def once(cls, interval, handler, *args, **kw):
        return cls(interval, 0, handler, *args, **kw)

    @classmethod
    def runOnce(cls, interval, handler, *args, **kw):
        t = cls.once(interval, handler, *args, **kw)
        t.start()
        return t

    @classmethod
    def forever(cls, interval, handler, *args, **kw):
        return cls(interval, -1, handler, *args, **kw)
    
    @classmethod
    def runForever(cls, interval, handler, *args, **kw):
        t = cls.forever(interval, handler, *args, **kw)
        t.start()
        return t


class TTTaskletTimer(TTTimer):
    def __init__(self, interval, repeatCount, handler, *args, **kw):
        super(TTTaskletTimer, self).__init__(interval, repeatCount, handler, *args, **kw)

    def _onTimeoutInTasklet(self):
        super(TTTaskletTimer, self)._onTimeout()

    def _onTimeout(self):
        TTTasklet.createTasklet(self._onTimeoutInTasklet)


