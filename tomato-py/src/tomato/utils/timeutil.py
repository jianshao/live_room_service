# -*- coding:utf-8 -*-
'''
Created on 2020年11月4日

@author: zhaojiangang
'''
import time


def datetimeToTimestamp(dt):
    return int(datetimeToTimestampFloat(dt))

def datetimeToTimestampFloat(dt):
    return time.mktime(dt.timetuple())

def currentTimestamp():
    return int(time.time())


