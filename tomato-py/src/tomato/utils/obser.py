# -*- coding:utf-8 -*-
'''
Created on 2016年12月21日

@author: zhaojiangang
'''

import time

from tomato.core.tasklet import TTTasklet
from tomato.utils import ttlog


class TTObserEvent(object):
    def __init__(self):
        self.timestamp = None
        self.source = None


def TTObserEventHandler(event):
    pass


class TTObservable(object):
    # key=eventType, value=TTObserEventHandler
    _listenerMap = None

    def on(self, eventType, handler, time=-1):
        self.addListener(eventType, handler)
        
    def off(self, eventType, handler):
        self.removeListener(eventType, handler)
        
    def addListener(self, eventType, handler, time=-1):
        if not self._listenerMap:
            self._listenerMap = {}
        
        ls = self._listenerMap.get(eventType)
        if not ls:
            ls = []
            self._listenerMap[eventType] = ls
        
        ls.append([handler, time])
        return self
    
    def removeListener(self, eventType, handler):
        if self._listenerMap:
            ls = self._listenerMap.get(eventType)
            if ls:
                for i, l in enumerate(ls):
                    if l[0] == handler:
                        del ls[i]
                        break
        return self
    
    def removeAllListener(self, eventType):
        if self._listenerMap:
            self._listenerMap.pop(eventType, None)
    
    def fire(self, event):
        assert(isinstance(event, TTObserEvent))
        event.timestamp = time.time()
        if not event.source:
            event.source = self
        
        curTask = TTTasklet.current()
        obserCtxKey = '__obser_ctx__.%s' % (id(self))
        obserCtx = curTask.userData.get(obserCtxKey)
        if not obserCtx:
            obserCtx = {'events':[], 'processing':False}
            curTask.userData[obserCtxKey] = obserCtx
        
        events = obserCtx['events']
        processing = obserCtx['processing']
        
        events.append(event)
        
        if not processing:
            obserCtx['processing'] = True
            try:
                while events:
                    evt = events.pop(0)
                    if self._listenerMap:
                        self._handleEvent(self._listenerMap, type(evt), evt)
            finally:
                obserCtx['processing'] = False
        else:
            if ttlog.isTraceEnabled():
                ttlog.trace('TTObservable.fire processing',
                            'event=', event,
                            'obserCtx=', obserCtx)
        return self
    
    def _handleEvent(self, listenerMap, eventType, event):
        if listenerMap:
            ls = listenerMap.get(eventType)
            if ttlog.isTraceEnabled():
                ttlog.trace('TTObservable._handleEvent',
                            'eventType=', eventType,
                            'event=', event,
                            'ls=', ls)
            if ls:
                tls = ls[:]
                for l in tls:
                    if l[1] != -1:
                        l[1] -= 1
                    if l[1] == 0:
                        self.removeListener(eventType, l[0])
                    try:
                        l[0](event)
                    except:
                        ttlog.error('TTObservable._handleEvent',
                                    'l=', l,
                                    'eventType=', type(event),
                                    'event=', event.__dict__)


if __name__ == '__main__':
    from tomato.core import mainloop
    from tomato.core.timer import TTTaskletTimer
    
    class TaskEvent(TTObserEvent):
        def __init__(self, name):
            super(TaskEvent, self).__init__()
            self.name = name

    class TaskEvent2(TTObserEvent):
        def __init__(self, name):
            super(TaskEvent2, self).__init__()
            self.name = name
            
    def task1(eventBus, eventBus2):
        eventBus.fire(TaskEvent('task2'))
    
    def task2(eventBus, eventBus2):
        ttlog.info('task2')
        raise Exception()
    
    def onTask1(event):
        ttlog.info('onTask1', event.name)
    
    def onTask2(event):
        ttlog.info('onTask2', event.name)
        raise Exception()
    
    def main():
        eventBus = TTObservable()
        eventBus2 = TTObservable()
        
        eventBus.on(TaskEvent, onTask1)
        eventBus.on(TaskEvent, onTask2)
        
        eventBus2.on(TaskEvent, onTask1)
        eventBus2.on(TaskEvent, onTask2)
        
        TTTaskletTimer.runOnce(1, task1, eventBus, eventBus2)
        TTTaskletTimer.runOnce(1, task1, eventBus, eventBus2)
        
#         TTTaskletTimer.runOnce(1, task2, eventBus)
    
    mainloop.run(main)


