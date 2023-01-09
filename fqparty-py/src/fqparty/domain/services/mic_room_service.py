# -*- coding:utf-8 -*-
'''
Created on 2020年10月22日

@author: zhaojiangang
'''

class MicRoomService(object):

    def gameStart(self, roomId, userId, gameId):
        '''
        开始游戏
        '''
        raise NotImplementedError

    
    def userEnterRoom(self, roomId, user, sessionDict, password):
        '''
        用户进入房间
        @param roomId: 哪个房间
        @param user: 进入房间的用户
        @param sessionDict: 当前连接相关
        @param password: 房间密码
        @return: RoomUser 
        '''
        raise NotImplementedError

    def userLeaveRoom(self, roomId, userId, reason):
        '''
        用户离开房间
        @param roomId: 哪个房间
        @param userId: 要离开房间的用户
        @param reason: 离开原因
        @return: RoomUser
        '''
        raise NotImplementedError

    def userOnMic(self, roomId, user, micId):
        '''
        用户上麦
        @param roomId: 哪个房间
        @param userId: 要上麦的用户
        @param micId: 要上哪个麦
        @param location: 团战要上麦的位置
        @return: RoomUser
        '''
        raise NotImplementedError
    
    def userLeaveMic(self, roomId, userId, reason, force=False):
        '''
        用户下麦
        @param roomId: 哪个房间
        @param userId: 要下麦的用户
        @param reason: 离开原因
        @param force: 是否强制离开
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
    
    def getRoomUserList(self, roomId, userId, listType):
        '''
        获取房间中所有用户的信息
        @param roomId: 哪个房间
        @param userId: 
        @param listType: 透传
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
    
    def lockMic(self, roomId, userId, micId, locked):
        '''
        锁麦/解除锁麦，只有管理员、房主、官方可以锁麦
        @param roomId: 哪个房间
        @param userId: 操作人
        @param micId: 麦id
        @return: RoomMic
        '''
        raise NotImplementedError
    
    def disableMic(self, roomId, userId, micId, disabled):
        '''
        禁麦/解除禁麦
        @param roomId: 哪个房间
        @param userId: 操作人
        @param micId: 麦id
        @return: RoomMic
        '''
        raise NotImplementedError
    
    def inviteMic(self, roomId, userId, inviteeUserId, micId, cancel):
        '''
        邀请别人上麦
        @param roomId: 哪个房间
        @param userId: 邀请人
        @param inviteeUserId: 被邀请人
        @param micId: 哪个麦
        @param cancel: 1 下麦；0 上麦
        '''
        raise NotImplementedError

    def countdownMic(self, roomId, userId, micId, duration):
        '''
        设置/取消麦倒计时，只有管理员、房主、官方可以锁麦
        @param roomId: 哪个房间
        @param userId: 操作人 
        @param micId: 哪个麦
        @param duration: 倒计时时长
        @return: RoomMic
        '''
        raise NotImplementedError
    
    def cancelCountdownMic(self, roomId, userId, micId):
        '''
        设置/取消麦倒计时，只有管理员、房主、官方可以锁麦
        @param roomId: 哪个房间
        @param userId: 操作人 
        @param micId: 哪个麦
        @return: RoomMic
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
    
    def sendMsgToRoom(self, roomId, userId, msgType, msg):
        '''
        发送消息到房间
        '''
        raise NotImplementedError
    
    def pushRoomInfo(self, roomId, userId):
        '''
        给用户发送房间信息
        '''
        raise NotImplementedError
    
    def syncMusicData(self, roomId, userId, msg):
        '''
        同步音乐数据
        '''
        raise NotImplementedError
    
    def disableUserMsg(self, roomId, userId, disabled):
        '''
        用户禁言
        '''
        raise NotImplementedError
    
    def kickoutUser(self, roomId, userId):
        '''
        踢用户出房间
        '''
        raise NotImplementedError
    
    def pushMsgToRoom(self, roomId, msg):
        '''
        发送消息给指定的房间
        '''
        raise NotImplementedError
    
    def pushMsgToAllRoom(self, msg, excludeRoomIds, excludeUserIds, type):
        '''
        发送消息给所有房间
        '''
        raise NotImplementedError
    
    def pushMsgToRoomUser(self, roomId, msg, userId):
        '''
        发送消息给指定的房间的指定用户
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

    def updatePKRoomData(self, roomId, pkMap, contributeMap):
        '''更新跨房pk信息'''
        raise NotImplementedError

    def notifyRoomAcrossPKStart(self, roomId, acrossPKData, pkRoomInfo):
        '''通知跨房pk开始'''
        raise NotImplementedError

    def notifyRoomSponsored(self, roomId):
        '''通知pk被其他房间邀请跨房pk'''
        raise NotImplementedError

    def invitePKList(self, roomId, userId):
        '''被邀请跨房pk列表'''
        raise NotImplementedError

    def createAcrossPK(self, roomId, userId, punishment, countdown):
        '''创建跨房pk'''
        raise NotImplementedError

    def cancelCreateAcrossPK(self, roomId, userId):
        '''取消创建跨房pk'''
        raise NotImplementedError

    def createAcorssPKList(self, roomId, userId):
        '''创建跨房pk列表'''
        raise NotImplementedError

    def sponsoreAcrossPK(self, roomId, userId, pkRoomId, punishment, countdown):
        '''发起跨房pk'''
        raise NotImplementedError

    def acceptAcrossPK(self, roomId, userId, pkRoomId):
        '''接受跨房pk'''
        raise NotImplementedError

    def refusedAcrossPK(self, roomId, userId, pkRoomId):
        '''拒绝跨房pk'''
        raise NotImplementedError

    def acorssPKingInfo(self, roomId, userId):
        '''跨房pk中信息'''
        raise NotImplementedError

    def joinPKLocation(self, roomId, user, location):
        '''
        用户加入pk的location
        @param roomId: 哪个房间
        @param user: 要上的用户
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

    def lockPKLocation(self, roomId, userId, location, locked):
        '''
        锁pk的location/解除锁pk的location，只有管理员、房主、官方可以锁麦
        @param roomId: 哪个房间
        @param userId: 操作人
        @param location: location id
        @param locked: 锁状态 True:锁 False:解
        @return: RoomMic
        '''
        raise NotImplementedError

    def disablePKLocation(self, roomId, userId, location, disabled):
        '''
        禁pk的location/解除禁pk的location
        @param roomId: 哪个房间
        @param userId: 操作人
        @param location: location id
        @param disabled: 禁状态 True:禁 False:不禁
        @return: RoomMic
        '''
        raise NotImplementedError

    def invitePKLocation(self, roomId, userId, inviteeUserId, location, cancel):
        '''
        邀请别人上pk的location
        @param roomId: 哪个房间
        @param userId: 邀请人
        @param inviteeUserId: 被邀请人
        @param location: 位置
        @param cancel: 1 下；0 上
        '''
        raise NotImplementedError





