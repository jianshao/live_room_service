# -*- coding:utf-8 -*-
'''
Created on 2022年3月4日

@author: zhaojiangang
'''

class ActiveMicManager(object):
    def findActiveRoom(self, roomId):
        '''
        根据roomId查找ActiveRoom
        '''
        raise NotImplementedError

    def removeActiveRoom(self, roomId):
        '''
        删除ActiveRoom
        '''
        raise NotImplementedError

    def findOrLoadActiveRoom(self, roomId, user=None):
        '''
        查找room，如果找不到就加载
        '''
        raise NotImplementedError

    def getActiveRoomMap(self):
        '''
        获取活跃房间map
        '''
        raise NotImplementedError

