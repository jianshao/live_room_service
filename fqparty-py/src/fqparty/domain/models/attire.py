# -*- coding:utf-8 -*-
'''
Created on 2020年11月4日

@author: zhaojiangang
'''

class Attire(object):
    def __init__(self, attrId):
        self.attrId = attrId
        self.pid = None
        self.imageIos = None
        self.imageAndroid = None
        self.svga = None
        self.color = ''
        self.multiple = ''


class AttireDao(object):
    def loadAttire(self, attrId):
        '''
        加载装伴
        '''
        raise NotImplementedError


