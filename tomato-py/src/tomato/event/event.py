# -*- coding:utf-8 -*-
'''
Created on 2021年1月6日

@author: zhaojiangang
'''
from tomato.utils.obser import TTObserEvent


class TTServerHeartbeatEvent(TTObserEvent):
    def __init__(self, heartbeatCount):
        super(TTServerHeartbeatEvent, self).__init__()
        self.heartbeatCount = heartbeatCount


