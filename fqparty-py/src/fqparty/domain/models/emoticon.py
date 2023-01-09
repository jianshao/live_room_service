# -*- coding:utf-8 -*-
'''
Created on 2020年11月9日

@author: zhaojiangang
'''

class Emoticon(object):
    def __init__(self, emoticonId):
        self.emoticonId = emoticonId
        self.animation = None
        self.gameImage = None


class EmoticonDao(object):
    def loadEmoticon(self, userId, emoticonId):
        '''
        根据Id加载表情
        '''
        raise NotImplementedError


