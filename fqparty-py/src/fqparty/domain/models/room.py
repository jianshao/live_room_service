# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''

class PKMode(object):
    # 团战pk
    TEAM_PK = 1
    # 跨房pk
    ACROSS_PK = 2


class PKTeam(object):
    # 红队
    RED_TEAM = 'red'
    # 蓝队
    BLUE_TEAM = 'blue'


class PKUser(object):
    '''
    pk的user
    '''
    def __init__(self, userId=None, nickname=None, avatar=None):
        # 用户数据
        self.userId = userId
        self.nickname = nickname
        self.avatar = avatar
        # 累计pk值
        self.totalPkValue = 0
        # 累计贡献值
        self.totalContributeValue = 0

    def toJson(self):
        return {
            'totalPkValue': self.totalPkValue,
            'totalContributeValue': self.totalContributeValue,
            'userId': self.userId,
            'nickname': self.nickname,
            'avatar': self.avatar
        }

    def fromJson(self, userDict):
        self.userId = userDict['userId']
        self.nickname = userDict['nickname']
        self.avatar = userDict['avatar']
        self.totalPkValue = userDict['totalPkValue']
        self.totalContributeValue = userDict['totalContributeValue']
        return self


class RoomAdmin(object):
    def __init__(self):
        # 管理员userId
        self.userId = 0
        # 管理员类型
        self.adminType = 0
        # 创建时间
        self.createDT = None
    
    def toDict(self):
        return {
            'userId':self.userId,
            'adminType':self.adminType,
            'createDT':0
        }
    
    def fromDict(self, d):
        self.userId = d['userId']
        self.adminType = d['adminType']
        self.createDT = None
        return self


class RoomType(object):
    '''
    房间类型
    '''
    def __init__(self, typeId):
        # 房间模式ID
        self.typeId = typeId
        # 父modeId
        self.parentId = None
        # 房间模式名称
        self.modeName = ''
        # 创建时间
        self.createTime = 0
        # 模式分类 1 普通用户 2公会用户
        self.modeType = 0
        # 状态：用于首页 1首页 2未首页(在创建列表没有)
        self.status = 0


class Room(object):
    '''
    房间基本信息
    '''
    def __init__(self, roomId):
        # 房间ID
        self.roomId = int(roomId)
        # 房间名称
        self.roomName = ''
        # 房主userId
        self.ownerUserId = 0
        # 房间密码
        self.password = ''
        # 是否开启了自动上麦
        self.isWheat = 0
        # 房间说明
        self.roomDesc = ''
        # 房间欢迎语
        self.roomWelcomes = ''
        # 房间背景图
        self.backgroundImage = ''
        # 工会ID
        self.guildId = ''
        # 创建时间，时间戳
        self.createTime = 0
        # 房间是否锁定0未锁定 1锁定
        self.roomLock = 0
        # 1 九麦模式2单麦模式
        self.roomMode = 1
        # roomMode
        self.roomType = None
        # 房间靓号
        self.prettyRoomId = 0
        # 房间管理员
        self.adminMap = {}

    @classmethod
    def encodeAdminMap(cls, adminMap):
        return [admin.toDict() for _, admin in adminMap.iteritems()]
    
    @classmethod
    def decodeAdminMap(cls, d):
        ret = {}
        if d and isinstance(d, list):
            for adminD in d:
                admin = RoomAdmin().fromDict(adminD)
                ret[admin.userId] = admin
        return ret
    
    def findAdmin(self, userId):
        return self.adminMap.get(userId)

    def toDict(self):
        return {
            'roomName':self.roomName,
            'ownerUserId':self.ownerUserId,
            'password':self.password,
            'isWheat':self.isWheat,
            'roomDesc':self.roomDesc,
            'roomWelcomes':self.roomWelcomes,
            'backgroundImage':self.backgroundImage,
            'guildId':self.guildId,
            'createTime':self.createTime,
            'roomLock':self.roomLock,
            'roomMode':self.roomMode,
            'roomType':self.roomType,
            'prettyRoomId':self.prettyRoomId,
            'admins':self.encodeAdminMap(self.adminMap)
        }
    
    def fromDict(self, d):
        self.roomName = d['roomName']
        self.ownerUserId = d['ownerUserId']
        self.password = d['password']
        self.isWheat = d['isWheat']
        self.roomDesc = d['roomDesc']
        self.roomWelcomes = d['roomWelcomes']
        self.backgroundImage = d['backgroundImage']
        self.guildId = d['guildId']
        self.createTime = d['createTime']
        self.roomLock = d['roomLock']
        self.roomMode = d['roomMode']
        self.roomType = d['roomType']
        self.prettyRoomId = d['prettyRoomId']
        self.adminMap = self.decodeAdminMap(d.get('admins', []))
        return self


class RoomDao(object):
    def loadRoom(self, roomId):
        '''
        加载房间
        @return: Room/None
        '''
        raise NotImplementedError

    def searchRoom(self, searchId):
        '''
        搜索房间 searchId可能是靓号
        @return: Room/None
        '''
        raise NotImplementedError


class RoomCacheDao(object):
    def loadRoom(self, roomId):
        '''
        加载房间
        @return: Room/None
        '''
        raise NotImplementedError
    
    def saveRoom(self, room):
        '''
        保存房间信息
        '''
        raise NotImplementedError


class RoomAdminDao(object):
    def loadRoomAdmins(self, roomId):
        '''
        加载房间管理员
        @return: list<RoomAdmin>
        '''
        raise NotImplementedError

        
class RoomTypeDao(object):
    def loadRoomMode(self, typeId):
        '''
        加载roomType
        @return: RoomType
        '''
        raise NotImplementedError


class RoomStatus(object):
    '''
    房间状态
    '''
    def __init__(self):
        # 禁止公屏
        self.disabledMsg = False
    
    def toDict(self):
        return {
            'disabledMsg':self.disabledMsg
        }
        
    def fromDict(self, d):
        self.disabledMsg = d.get('disabledMsg', False)
        return self


class RoomStatusDao(object):
    def loadRoomStatus(self, roomId):
        '''
        加载房间状态
        '''
        raise NotImplementedError
    
    def saveRoomStatus(self, roomId, roomStatus):
        '''
        保存房间状态
        '''
        raise NotImplementedError


class RoomMicStatus(object):
    def __init__(self, micId=0):
        # 麦位ID
        self.micId = micId
        # 是否锁麦
        self.locked = False
        # 是否禁麦
        self.disabled = False
        # 开始时间
        self.countdownTime = 0
        # 倒计时时间
        self.countdownDuration = 0
        # 邀请的用户ID
        self.inviteUserId = 0
        self.inviteRoomId = 0
        # 麦位上的用户ID
        self.userId = 0
    
    def toDict(self):
        return {
            'micId':self.micId,
            'locked':self.locked,
            'disabled':self.disabled,
            'countdownTime':self.countdownTime,
            'countdownDuration':self.countdownDuration,
            'inviteUserId':self.inviteUserId,
            'inviteRoomId':self.inviteRoomId,
            'userId':self.userId,
        }
        
    def fromDict(self, d):
        self.micId = d['micId']
        self.locked = d['locked']
        self.disabled = d['disabled']
        self.countdownTime = d['countdownTime']
        self.countdownDuration = d['countdownDuration']
        self.inviteUserId = d['inviteUserId']
        self.inviteRoomId = d['inviteRoomId']
        self.userId = d['userId']
        return self


class RoomMicStatusDao(object):
    def loadRoomMicStatusMap(self, roomId):
        '''
        加载房间麦位列表
        @return: map<micId, RoomMicStatus>
        '''
        raise NotImplementedError
    
    def saveRoomMicStatusMap(self, roomId, roomMicStatusMap):
        '''
        保存房间麦位列表
        '''
        raise NotImplementedError

    def loadRoomMicStatus(self, roomId, micId):
        '''
        加载房间麦位
        @return: map<micId, RoomMicStatus>
        '''
        raise NotImplementedError

    def saveRoomMicStatus(self, roomId, roomMicStatus):
        '''
        保存房间麦位
        '''
        raise NotImplementedError

    def removeRoomAllMicStatus(self, roomId):
        '''
        删除房间麦位
        '''
        raise NotImplementedError
    
    def removeRoomMicStatus(self, roomId, micId):
        '''
        删除某个麦位
        '''
        raise NotImplementedError


class MicUserStatus(object):
    def __init__(self, userId=0):
        # userId
        self.userId = userId
        # 麦位ID
        self.micId = 0
        # 上麦时间
        self.onMicTime = 0
        # 心跳时间
        self.heartbeatTime = 0
    
    def toDict(self):
        return {
            'userId': self.userId,
            'micId':self.micId,
            'onMicTime':self.onMicTime,
            'heartbeatTime':self.heartbeatTime
        }
        
    def fromDict(self, d):
        self.userId = d['userId']
        self.micId = d['micId']
        self.onMicTime = d['onMicTime']
        self.heartbeatTime = d['heartbeatTime']
        return self


class MicUserStatusDao(object):
    def loadMicUserStatusMap(self, roomId, userIds):
        '''
        加载房间麦位map
        '''
        raise NotImplementedError

    def saveMicUserStatusMap(self, roomId, micUserStatusMap):
        '''
        保存麦位用户状态map
        '''
        raise NotImplementedError

    def loadMicUserStatus(self, roomId, userId):
        '''
        加载麦位用户状态
        @return: MicUserStatus or None
        '''
        raise NotImplementedError
    
    def saveMicUserStatus(self, roomId, userId, status):
        '''
        保存麦位用户状态
        '''
        raise NotImplementedError
    
    def removeMicUserStatus(self, roomId, userId):
        '''
        删除麦位用户状态
        '''
        raise NotImplementedError


class RoomUserStatus(object):
    def __init__(self):
        # 是否被禁言
        self.disabledMsg = False
        # 进房时间
        self.enterTime = 0
        # 最后心跳时间
        self.heartbeatTime = 0
    
    def toDict(self):
        return {
            'disabledMsg':self.disabledMsg,
            'enterTime':self.enterTime,
            'heartbeatTime':self.heartbeatTime
        }
    
    def fromDict(self, d):
        self.disabledMsg = d['disabledMsg']
        self.enterTime = d['enterTime']
        self.heartbeatTime = d['heartbeatTime']
        return self


class RoomUserStatusDao(object):
    def loadRoomUserStatus(self, roomId, userId):
        '''
        加载房间用户状态
        '''
        raise NotImplementedError
    
    def saveRoomUserStatus(self, roomId, userId, status):
        '''
        保存房间用户状态
        '''
        raise NotImplementedError
    
    def removeRoomUserStatus(self, roomId, userId):
        '''
        删除房间用户
        '''
        raise NotImplementedError


class RoomUserRankDao(object):
    def getRoomRickDayValue(self, userId, roomId):
        '''
        @return: user day consume
        '''
        raise NotImplementedError


