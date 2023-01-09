# -*- coding:utf-8 -*-
'''
Created on 2022年1月24日

@author: zhaojiangang
'''
from fqparty.const import ErrorCode, AdminTypes
from tomato.core.exceptions import TTException
from tomato.utils.orderdedict import TTOrderedDict
from tomato.config import configure
from tomato.utils import timeutil
from fqparty.domain.models.room import RoomUserStatus, PKUser, PKTeam


class RoomUserInfo(object):
    def __init__(self, user, sessionInfo, roomUserStatus, micUserStatus, roomMicStatus):
        self.user = user
        self.sessionInfo = sessionInfo
        self.roomUserStatus = roomUserStatus
        self.micUserStatus = micUserStatus
        self.roomMicStatus = roomMicStatus
        

class RoomUserInfoLoader(object):
    def loadRoomUserInfo(self, roomId, userId):
        '''
        加载
        '''
        raise NotImplementedError


class RoomUserInfoLoaderImpl(RoomUserInfoLoader):
    def __init__(self, userCacheDao, sessionInfoDao, roomUserStatusDao, micUserStatusDao, roomMicStatusDao):
        self._userCacheDao = userCacheDao
        self._sessionInfoDao = sessionInfoDao
        self._roomUserStatusDao = roomUserStatusDao
        self._micUserStatusDao = micUserStatusDao
        self._roomMicStatusDao = roomMicStatusDao

    def loadRoomUserInfo(self, roomId, userId):
        '''
        加载
        '''
        user = self._userCacheDao.loadUser(userId)
        if not user:
            return None
        sessionInfo = self._sessionInfoDao.loadSessionInfo(userId) or {}
        roomUserStatus = self._roomUserStatusDao.loadRoomUserStatus(roomId, userId) or RoomUserStatus()
        micUserStatus = self._micUserStatusDao.loadMicUserStatus(roomId, userId)
        roomMicStatus = self._roomMicStatusDao.loadRoomMicStatus(roomId, micUserStatus.micId) if micUserStatus and micUserStatus.micId else None
        return RoomUserInfo(user, sessionInfo or {}, roomUserStatus, micUserStatus, roomMicStatus)


class RoomMicInfo(object):
    def __init__(self, status, user, heartValue):
        self.status = status
        self.user = user
        self.heartValue = heartValue


class RoomTeamPKInfo(object):
    def __init__(self, status, pkLocationMap, userCacheDao):
        self.status = status
        self.userCacheDao = userCacheDao
        self.pkLocationMap = pkLocationMap

    def findUser(self, userId):
        user = self.userCacheDao.loadUser(userId)
        return PKUser(user.userId, user.nickname, user.avatar)

    def getPKLocation(self, location):
        return self.pkLocationMap.get(location)

    def getPKValue(self, userId):
        userId = str(userId)
        if userId in self.status.bluePKMap:
            return self.status.bluePKMap[userId]
        elif userId in self.status.redPKMap:
            return self.status.redPKMap[userId]
        return 0

    def getFirstCharmUser(self):
        #参与pk的主播收到打赏礼物累计总金额（私聊送礼不参与统计）最高的用户
        base = 0
        firstUserId = None
        for userId, pkValue in self.status.redPKMap.iteritems():
            if pkValue >= base:
                base = pkValue
                firstUserId = userId

        for userId, pkValue in self.status.bluePKMap.iteritems():
            if pkValue >= base:
                base = pkValue
                firstUserId = userId

        if firstUserId is None or base == 0:
            return None

        user = self.findUser(firstUserId)
        user.totalPkValue = base
        return user

    def getCharmUsers(self, team):
        #红/蓝队pk值最高的4个
        pkMap = self.status.redPKMap if team == PKTeam.RED_TEAM else self.status.bluePKMap
        newMap = sorted(pkMap.items(), key=lambda x: x[1], reverse=True)

        users = []
        for userId, pkValue in newMap:
            if len(users) >= 4: break
            user = self.findUser(userId)
            user.totalPkValue = pkValue
            users.append(user)

        return users

    def getMVPUser(self):
        # 打赏给参与PK主播的主播礼物累计总金额（私聊送礼不参与统计）最高的用户 主持麦参与统计
        base = 0
        mvpUserId = None

        for userId, contribute in self.status.blueContributeMap.iteritems():
            if contribute >= base:
                base = contribute
                mvpUserId = userId

        for userId, contribute in self.status.redContributeMap.iteritems():
            if contribute >= base:
                base = contribute
                mvpUserId = userId

        for userId, contribute in self.status.hostContributeMap.iteritems():
            if contribute >= base:
                base = contribute
                mvpUserId = userId

        if mvpUserId is None or base == 0:
            return None

        mvpUser = self.findUser(mvpUserId)
        mvpUser.totalContributeValue = base
        return mvpUser

    def getMVPUsers(self, winPK):
        # 贡献榜为获胜一方1-4名累计贡献最大的用户
        if not winPK:
            return []

        contributeMap = self.status.redContributeMap if winPK == PKTeam.RED_TEAM else self.status.blueContributeMap
        newMap = sorted(contributeMap.items(), key=lambda x:x[1], reverse=True)

        users = []
        for userId, contribute in newMap:
            if len(users) >= 4:break
            user = self.findUser(userId)
            user.totalContributeValue = contribute
            users.append(user)

        return users


class RoomAcrossPKInfo(object):
    def __init__(self, roomId, status, userCacheDao):
        self.roomId = roomId
        self.status = status
        self.userCacheDao = userCacheDao

        # 贡献榜 团战期间送礼物人的统计map(roomId, (userId, 贡献值)) 红队vs蓝队
        self.contributeMap = self.status.contributeMap

        # pk值榜 收礼物人的统计map(roomId, (userId, pk值)) 红队vs蓝队
        self.pkMap = self.status.pkMap

    @property
    def acrossPK(self):
        return self.status.acrossPK

    @property
    def startTime(self):
        return self.status.startTime

    @property
    def punishment(self):
        return self.status.acrossPK.punishment

    @property
    def countdown(self):
        return self.status.acrossPK.countdown

    def findUser(self, userId):
        user = self.userCacheDao.loadUser(userId)
        return PKUser(user.userId, user.nickname, user.avatar)

    def getTeam(self):
        return PKTeam.RED_TEAM if self.roomId == self.acrossPK.createRoomId else PKTeam.BLUE_TEAM

    def getTotalPKValue(self, team):
        #参与pk的主播收到打赏礼物累计总金额（私聊送礼不参与统计）最高的用户
        redPKMap = self.pkMap[self.acrossPK.createRoomId]
        bluePKMap = self.pkMap[self.acrossPK.pkRoomId]

        pkMap = redPKMap if team == PKTeam.RED_TEAM else bluePKMap
        return sum(pkMap.values())

    def getCharmUsers(self, team):
        # 红/蓝队pk值最高的3个
        redPKMap = self.pkMap[self.acrossPK.createRoomId]
        bluePKMap = self.pkMap[self.acrossPK.pkRoomId]

        pkMap = redPKMap if team == PKTeam.RED_TEAM else bluePKMap
        if not pkMap or len(pkMap) == 0:
            return []

        newMap = sorted(pkMap.items(), key=lambda x: x[1], reverse=True)
        users = []
        for userId, pkValue in newMap:
            if len(users) >= 4: break
            user = self.findUser(userId)
            user.totalPkValue = pkValue
            users.append(user)

        return users

    def getMVPUsers(self, winPK):
        # 贡献榜为获胜一方1-3名累计贡献最大的用户
        redContributeMap = self.contributeMap[self.acrossPK.createRoomId]
        blueContributeMap = self.contributeMap[self.acrossPK.pkRoomId]

        contributeMap = redContributeMap if winPK == PKTeam.RED_TEAM else blueContributeMap
        if not contributeMap or len(contributeMap) == 0:
            return []

        newMap = sorted(contributeMap.items(), key=lambda x: x[1], reverse=True)
        users = []
        for userId, contribute in newMap:
            if len(users) >= 3: break
            user = self.findUser(userId)
            user.totalContributeValue = contribute
            users.append(user)

        return users


class ChatInfo(object):
    def __init__(self):
        self.lastChatTime = 0
        self.chatCount = 0
    
    def isSameMinute(self, ts1, ts2):
        return ts1 / 60 == ts2 / 60
    
    def adjust(self, curTime):
        if not self.isSameMinute(curTime, self.lastChatTime):
            self.lastChatTime = curTime
            self.chatCount = 0
    
    def incrChatCount(self, curTime):
        self.adjust(curTime)
        self.chatCount += 1


class RoomUser(object):
    '''
    活跃的房间用户
    '''
    def __init__(self, roomId, user, status, sessionInfo, dayConsume=0):
        # 房间Id
        self.roomId = roomId
        # 用户数据
        self.user = user
        # 房间用户状态
        self.status = status
        # sessionInfo
        self.sessionInfo = sessionInfo
        # 当日消费
        self.dayConsume = dayConsume
        # 最后聊天时间
        self.chatInfo = ChatInfo()
        # 上次发送心跳的时间
        self.lastHeartbeatTime = timeutil.currentTimestamp()
    
    @property
    def userId(self):
        return self.user.userId
    
    @property
    def frontendId(self):
        return self.sessionInfo.get('frontendId')
    

class RoomUserManager(object):
    def getAllUserCount(self):
        '''
        获取所有用户数量
        '''
        raise NotImplementedError
    
    def getUserCountByRoom(self, roomId):
        '''
        获取roomId房间的用户数量
        '''
        raise NotImplementedError
        
    def findRoomUser(self, userId):
        '''
        根据userId查找RoomUser
        @return: RoomUser or None
        '''
        raise NotImplementedError
    
    def addRoomUser(self, roomUser):
        '''
        添加RoomUser
        '''
        raise NotImplementedError
    
    def removeRoomUser(self, roomUser):
        '''
        删除RoomUser
        '''
        raise NotImplementedError
    
    def getRoomUsersMap(self):
        '''
        获取用户
        @return: Map<userId, RoomUser>
        '''
        raise NotImplementedError
    
    def getRoomUsersByRoomId(self, roomId):
        '''
        获取某个房间的用户
        @return: set<RoomUser> or None
        '''
        raise NotImplementedError
    
    def getRoomIdUserSet(self):
        '''
        @return: map<roomId, set<RoomUser>>
        '''
        raise NotImplementedError


class RoomUserManagerImpl(RoomUserManager):
    def __init__(self):
        # 活跃用户 map<userId, RoomUser>
        self._userMap = {}
        # map<roomId, set<RoomUser>>
        self._roomId2UserSet = {}
    
    def getAllUserCount(self):
        return len(self._userMap)
    
    def getUserCountByRoom(self, roomId):
        roomUserSet = self._roomId2UserSet.get(roomId)
        return len(roomUserSet) if roomUserSet else 0
    
    def findRoomUser(self, userId):
        return self._userMap.get(userId)
    
    def addRoomUser(self, roomUser):
        assert(not self.findRoomUser(roomUser.userId))
        self._userMap[roomUser.userId] = roomUser
        roomUserSet = self._roomId2UserSet.get(roomUser.roomId)
        if not roomUserSet:
            roomUserSet = set()
            self._roomId2UserSet[roomUser.roomId] = roomUserSet
        roomUserSet.add(roomUser)
    
    def removeRoomUser(self, roomUser):
        assert(self.findRoomUser(roomUser.userId) == roomUser)
        self._userMap.pop(roomUser.userId, None)
        roomUserSet = self._roomId2UserSet.get(roomUser.roomId)
        if roomUserSet:
            roomUserSet.discard(roomUser)
            if not roomUserSet:
                self._roomId2UserSet.pop(roomUser.roomId)
    
    def getRoomUsersMap(self):
        return self._userMap
    
    def getRoomUsersByRoomId(self, roomId):
        return self._roomId2UserSet.get(roomId, None)
    
    def getRoomIdUserSet(self):
        return self._roomId2UserSet


class ActiveRoom(object):
    '''
    活跃房间
    '''
    def __init__(self, room, ownerUser, top3UserIds):
        # 房间信息
        self.room = room
        # 房主 User 对象
        self.ownerUser = ownerUser
        # 前三
        self.top3UserIds = top3UserIds
    
    @property
    def roomId(self):
        return self.room.roomId
    
    @property
    def ownerUserId(self):
        return self.ownerUser.userId

    @property
    def platformNotice(self):
        return configure.loadJson('server.fqparty.global', {}).get('platformNotice')
    
    def findAdmin(self, userId):
        return self.room.findAdmin(userId)
    
    def isOwner(self, userId):
        return self.ownerUser.userId == userId
    
    def getUserIdentity(self, userId):
        if userId == self.ownerUser.userId:
            return AdminTypes.OWNER

        admin = self.findAdmin(userId)
        if admin:
            return admin.adminType

        return AdminTypes.USER


class ActiveRoomManager(object):
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


class ActiveRoomManagerImpl(ActiveRoomManager):
    def __init__(self, roomDao, userDao):
        # map<roomId, ActiveRoom>
        self._activeRoomMap = TTOrderedDict()
    
    def findActiveRoom(self, roomId):
        roomId = int(roomId)
        return self._activeRoomMap.get(roomId)

    def removeActiveRoom(self, roomId):
        roomId = int(roomId)
        return self._activeRoomMap.pop(roomId, None)
        
    def findOrLoadActiveRoom(self, roomId, user=None):
        '''
        查找room
        '''
        roomId = int(roomId)
        activeRoom = self.findActiveRoom(roomId)
        isLoad = False
        if not activeRoom:
            activeRoom = self._loadActiveRoom(roomId, user)
            isLoad = True
            self._activeRoomMap[roomId] = activeRoom
        return activeRoom, isLoad
    
    def getActiveRoomMap(self):
        return self._activeRoomMap
    
    def _loadActiveRoom(self, roomId, user):
        from fqparty.servers.room import RoomServer
        room = RoomServer.roomDao.loadRoom(roomId)
        if not room:
            raise TTException(ErrorCode.ROOM_NOT_EXISTS)
        
        if user and room.ownerUserId == user.userId:
            ownerUser = user
        else:
            ownerUser = RoomServer.userDao.loadUser(room.ownerUserId)
            if not ownerUser:
                raise TTException(ErrorCode.ROOM_NOT_EXISTS)

        top3UserIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(roomId, 0, 3)
        return ActiveRoom(room, ownerUser, top3UserIds)


class RoomServerOnlineUserDao(object):
    def loadRoomOnlineUsers(self, serverId):
        '''
        加载serverId在线的所有用户
        return list<(userId, roomId)>
        '''
        raise NotImplementedError
    
    def addRoomOnlineUser(self, serverId, userId, roomId):
        '''
        添加用户ID
        '''
        raise NotImplementedError
    
    def removeRoomOnlineUser(self, serverId, userId):
        '''
        删除在线userId
        '''
        raise NotImplementedError


class RoomOnlineUserListDao(object):
    def setRoomOnlineUser(self, roomId, userId, score):
        '''
        添加用户到roomId所在房间
        '''
        raise NotImplementedError
    
    def removeRoomOnlineUser(self, roomId, userId):
        '''
        删除用户
        '''
        raise NotImplementedError
    
    def getRoomOnlineUserIds(self, roomId, pos, count):
        '''
        获取roomId房间pos位置开始count个用户Id
        '''
        raise NotImplementedError
    
    def getRoomOnlineUserCount(self, roomId):
        '''
        获取房间在线用户数量
        '''
        raise NotImplementedError

    def existsRoomOnlineUser(self, roomId, userId):
        '''
        查询用户是否在线
        '''
        raise NotImplementedError


class MicServerActiveRoomDao(object):
    def loadActiveRooms(self, serverId):
        '''
        加载serverId活跃的房间
        return list<(roomId)>
        '''
        raise NotImplementedError

    def addActiveRoom(self, serverId, roomId):
        '''
        添加房间id
        '''
        raise NotImplementedError

    def removeActiveRoom(self, serverId, roomId):
        '''
        删除活跃的房间Id
        '''
        raise NotImplementedError
