# -*- coding:utf-8 -*-
'''
Created on 2020年10月30日

@author: zhaojiangang
'''

class UserService(object):
    def login(self, userId, sessionInfo):
        '''
        用户登录
        '''
        raise NotImplementedError

    def logout(self, userId, reason):
        '''
        用户登出
        reason为长连接断开的原因
        '''
        raise NotImplementedError

    def userHeartbeat(self, userId, pkg):
        '''
        用户心跳
        '''
        raise NotImplementedError
    
    def userActiveHeartbeat(self, userId, pkg):
        '''
        用户主动心跳
        '''
        raise NotImplementedError
    
    def findActiveUser(self, userId):
        '''
        查找活跃用户
        '''
        raise NotImplementedError
    
    def enterRoom(self, userId, roomId, password):
        '''
        用户进入房间
        '''
        raise NotImplementedError
    
    def leaveRoom(self, userId, roomId, reason, reasonInfo=None):
        '''
        用户离开房间
        '''
        raise NotImplementedError
    
    def updateUserInfo(self, userId):
        '''
        更新用户数据
        '''
        raise NotImplementedError
    
    def getUserInfo(self, userId):
        '''
        获取用户数据
        '''
        raise NotImplementedError
    
    def checkUserLogin(self, userId, msg):
        '''
        检查用户token
        '''
        raise NotImplementedError

    def getUserRoomLocation(self, userId):
        '''获取用户当前位置'''
        raise NotImplementedError


