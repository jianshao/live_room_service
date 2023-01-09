# -*- coding:utf-8 -*-
'''
Created on 2020年10月22日

@author: zhaojiangang
'''

class RoomService(object):
    def isUserInRoom(self, roomId, userId):
        '''
        检查用户是否在房间
        '''
        raise NotImplementedError
    
    def userEnterRoom(self, roomId, userId, password):
        '''
        用户进入房间
        @param roomId: 哪个房间
        @param user: 进入房间的用户
        @param password: 房间密码
        @return: RoomUser 
        '''
        raise NotImplementedError

    def userLeaveRoom(self, roomId, userId, reason, reasonInfo):
        '''
        用户离开房间
        @param roomId: 哪个房间
        @param userId: 要离开房间的用户
        @param reason: 离开原因
        @return: RoomUser
        '''
        raise NotImplementedError

    def userOffline(self, roomId, userId):
        '''
        用户断线
        '''
        raise NotImplementedError
    
    def userHeartbeat(self, roomId, userId):
        '''
        用户心跳
        '''
        raise NotImplementedError
    
    def userOnMic(self, roomId, userId, micId):
        '''
        用户上麦
        @param roomId: 哪个房间
        @param userId: 要上麦的用户
        @param micId: 要上哪个麦
        @return: RoomUser
        '''
        raise NotImplementedError
    
    def userLeaveMic(self, roomId, userId, reason):
        '''
        用户下麦
        @param roomId: 哪个房间
        @param userId: 要下麦的用户
        @param reason: 离开原因
        @return: RoomUser
        '''
        raise NotImplementedError
    
    def pushRoomInfo(self, roomId, userId):
        '''
        给用户发送房间信息
        '''
        raise NotImplementedError
    
    def sendMsgToRoom(self, roomId, userId, msgType, msg):
        '''
        发送消息到房间
        '''
        raise NotImplementedError
    
    def disableUserMsg(self, roomId, userId, disabled):
        '''
        用户禁言
        '''
        raise NotImplementedError
    
    def getUserMic(self, roomId, userId):
        '''
        获取用户麦位
        '''
        raise NotImplementedError
    
    def disableRoomMsg(self, roomId, userId, disabled):
        '''
        开启/关闭公屏
        @param roomId: 要开启/关闭的房间
        @param userId: 哪个用户开启/关闭
        @param disabled: True: 开 False: 关
        '''
        raise NotImplementedError
    
    def joinPKLocation(self, roomId, userId, location):
        '''
        用户加入pk的location
        @param roomId: 哪个房间
        @param userId: 要上的用户
        @param location: 团战要上的位置
        @return: RoomUser
        '''
        raise NotImplementedError

    def leavePKLocation(self, roomId, userId, reason):
        '''
        用户下pk的location
        @param roomId: 哪个房间
        @param userId: 要下麦的用户
        @param reason: 离开原因
        @return: RoomUser
        '''
        raise NotImplementedError
    
    def getRoomUserInfo(self, roomId, userId, queryUserId):
        '''
        获取房间中某个用户的信息
        @param roomId: 哪个房间
        @param userId: 
        @param queryUserId: 要查询的userId
        '''
        raise NotImplementedError
    
    def getRoomUserListAll(self, roomId, userId, pageIndex, pageNum):
        '''
        获取房间中所有用户的信息第2版
        @param roomId: 哪个房间
        @param userId:
        @param pageIndex: 第几页
        @param pageNum: 一页取几个
        '''
        raise NotImplementedError

    def getRoomUserListThree(self, roomId, userId, num):
        '''
        获取房间中前num用户的信息
        @param roomId: 哪个房间
        @param userId:
        @param num: 默认3
        '''
        raise NotImplementedError
    
    def syncMusicData(self, roomId, userId, msg):
        '''
        同步音乐数据
        '''
        raise NotImplementedError
    
    def updateUserInfo(self, roomId, userId):
        '''
        更新用户信息
        '''
        raise NotImplementedError
    
    def pushMsgToRoom(self, roomId, msg, msgType):
        '''
        发送消息给指定的房间
        '''
        raise NotImplementedError
    
    def pushMsgToAllRoom(self, msg, excludeRoomIds, excludeUserIds, msgType):
        '''
        发送消息给所有房间
        '''
        raise NotImplementedError
    
    def lockRoom(self, roomId, locked):
        '''
        锁/解锁房间
        '''
        raise NotImplementedError
    
    def updateRoomData(self, roomId, dataType):
        '''
        更新房间信息
        '''
        raise NotImplementedError




