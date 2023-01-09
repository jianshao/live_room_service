# -*- coding:utf-8 -*-
'''
Created on 2020年11月10日

@author: zhaojiangang
'''

class Attention(object):
    def __init__(self):
        self.userId = 0
        self.userIdEd = 0
        self.attentionTime = 0


class AttentionDao(object):
    def loadAttention(self, userId, userIdEd):
        '''
        加载userId关注userIdEd的关注关系
        @return: Attention
        '''
        raise NotImplementedError


