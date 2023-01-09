# -*- coding:utf-8 -*-
'''
Created on 2020年10月31日

@author: zhaojiangang
'''

class RoomLocation(object):
    '''
    用户在房间的记录
    '''
    def __init__(self, roomId=0, serverId=None):
        # 在哪个房间
        self.roomId = roomId
        # 在哪个房间进程
        self.serverId = serverId


class RoomLocationDao(object):
    def loadRoomLocation(self, userId):
        '''
        加载location
        @param userId: 哪个用户
        @return: RoomLocation or None
        '''
        raise NotImplementedError
    
    def saveRoomLocation(self, userId, location):
        '''
        保存location
        @param userId: 哪个用户
        @param location: location
        '''
        raise NotImplementedError
    
    def removeRoomLocation(self, userId):
        '''
        删除location
        @param userId: 哪个用户
        '''
        raise NotImplementedError


