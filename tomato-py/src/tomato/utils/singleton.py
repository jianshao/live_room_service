# -*- coding=utf-8 -*-
'''
Created on 2017年12月10日

@author: zhaojiangang
'''
import functools


class TTSingleton(type):
    def __init__(self, name, bases, dic):
        super(TTSingleton, self).__init__(name, bases, dic)
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = super(TTSingleton, self).__call__(*args, **kwargs)
        return self.instance


def singleton(cls):
    instances = {}
    @functools.wraps(cls)
    def getinstance(*args, **kw): 
        if cls not in instances:  
            instances[cls] = cls(*args, **kw)  
        return instances[cls]  
    return getinstance


