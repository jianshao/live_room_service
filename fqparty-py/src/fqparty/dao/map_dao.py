# -*- coding=utf-8 -*-
'''
Created on 2018年2月11日

@author: zhaojiangang
'''


class MapDao(object):
    def getValue(self, key):
        '''
        在map中查找key的值
        @return: value
        '''
        raise NotImplementedError
    
    def isKeyExists(self, key):
        '''
        判断key是否在map中
        @return: True or False
        '''
        raise NotImplementedError

    def setValue(self, key, value):
        '''
        在map中设置key的值为value
        '''
        raise NotImplementedError
    
    def removeValue(self, key):
        '''
        在map中删除key
        '''
        raise NotImplementedError


