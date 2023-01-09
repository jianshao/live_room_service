# -*- coding:utf-8 -*-
'''
Created on 2020年11月2日

@author: zhaojiangang
'''
import binascii
from datetime import datetime

from fqparty.dao.map_dao import MapDao
from fqparty.domain.models.emoticon import Emoticon, EmoticonDao
from fqparty.domain.models.location import RoomLocationDao, RoomLocation
from fqparty.domain.models.room import RoomCacheDao, Room, RoomMicStatusDao, \
    RoomMicStatus, RoomUserStatusDao, RoomUserStatus, RoomStatusDao, RoomStatus, \
    MicUserStatusDao, MicUserStatus, RoomUserRankDao
from fqparty.domain.models.user import User, UserCacheDao, SessionInfoDao, UserFrontDao
from fqparty.domain.room.room import RoomServerOnlineUserDao, RoomOnlineUserListDao, MicServerActiveRoomDao
from fqparty.domain.mic.room_team_pk import RoomTeamPKStatus, RoomTeamPKStatusDao, RoomPKLocationDao, RoomPKLocation
from fqparty.domain.mic.room_across_pk import RoomAcrossPKStatus, RoomAcrossPKStatusDao
from tomato.utils import strutil, ttlog


class DaoRedis(object):
    def __init__(self, connections):
        self._connections = connections if isinstance(connections, list) else [connections]

    def getConnection(self, key):
        index = 0
        if len(self._connections) > 1:
            if isinstance(key, int):
                index = len(self._connections) % key
            else:
                index = binascii.crc32('%s' % (key)) % len(self._connections)
        return self._connections[index]


class MapDaoRedis(MapDao):
    def __init__(self, conn):
        self.conn = conn

    def getValue(self, key):
        '''
        在map中查找key的值
        @return: value
        '''
        return self.conn.send('get', key)
    
    def isKeyExists(self, key):
        '''
        判断key是否在map中
        @return: True or False
        '''
        return self.conn.send('exists', key)
    
    def setValue(self, key, value):
        '''
        在map中设置key的值为value
        '''
        return self.conn.send('set', key, value)
    
    def removeValue(self, key):
        '''
        在map中删除key
        '''
        return self.conn.send('del', key)
    

class RoomLocationDaoRedis(RoomLocationDao):
    def __init__(self, redisDao):
        super(RoomLocationDaoRedis, self).__init__()
        self._redisDao = redisDao

    def loadRoomLocation(self, userId):
        roomId = self._redisDao.getConnection(userId).send('hget', 'user_current_room', userId)
        try:
            if roomId:
                return RoomLocation(int(roomId))
        except:
            ttlog.warn('Bad location roomId',
                       'userId=', userId,
                       'roomId=', (roomId, type(roomId)))
        return None
    
    def saveRoomLocation(self, userId, location):
        self._redisDao.getConnection(userId).send('hset', 'user_current_room', userId, location.roomId)
    
    def removeRoomLocation(self, userId):
        self._redisDao.getConnection(userId).send('hdel', 'user_current_room', userId)

    def getStaticConfVersion(self, userId):
        return self._redisDao.getConnection(userId).send('get', 'static_conf_version')


class EmoticonDaoRedis(EmoticonDao):
    def __init__(self, redisDao):
        super(EmoticonDaoRedis, self).__init__()
        self._redisDao = redisDao

    def loadEmoticon(self, userId, emoticonId):
        '''
        根据Id加载表情
        '''
        ret = None
        res = self._redisDao.getConnection(userId).send('get', 'emoticon_conf')
        if not res:
            return ret

        res = strutil.jsonLoads(res)
        for item in res:
            if item['id'] == emoticonId:
                ret = Emoticon(item['id'])
                ret.animation = item.get('animation')
                ret.gameImage = item.get('gameImages')
                break
        return ret

    def getMaxRoomCount(self):
        '''
        获取房间最大人数配置
        '''
        maxCount = self._redisDao.getConnection(0).send('hget', 'room_conf', 'max_count')
        return int(maxCount) if maxCount else 50000


class RoomUserRankDaoRedis(RoomUserRankDao):
    def __init__(self, redisDao):
        super(RoomUserRankDaoRedis, self).__init__()
        self._redisDao = redisDao

    def getRoomRickDayValue(self, roomId, userId):
        dt = datetime.now()
        key = 'Rich_Day_%s_%s' % (str(roomId), dt.strftime('%Y%m%d'))
        return self._redisDao.getConnection(roomId).send('ZSCORE', key, userId)


class UserFrontDaoRedis(UserFrontDao):
    def __init__(self, redisDao):
        super(UserFrontDaoRedis, self).__init__()
        self._redisDao = redisDao
    
    @classmethod
    def buildKey(cls, userId):
        return 'user:%s' % (userId)

    def getFrontendId(self, userId):
        '''
        获取用户长连接的serverId
        '''
        return self._redisDao.getConnection(userId).send('hget', self.buildKey(userId), 'conn')

    def setFrontendId(self, userId, frontendId):
        '''
        设置用户长连接serverId
        '''
        return self._redisDao.getConnection(userId).send('hset', self.buildKey(userId), 'conn', frontendId)
    
    def removeFrontendId(self, userId):
        '''
        删除用户长连接serverId
        '''
        return self._redisDao.getConnection(userId).send('hdel', self.buildKey(userId), 'conn')


class SessionInfoDaoRedis(SessionInfoDao):
    def __init__(self, redisDao):
        super(SessionInfoDaoRedis, self).__init__()
        self._redisDao = redisDao
    
    @classmethod
    def buildKey(cls, userId):
        return 'user:%s' % (userId)
    
    def loadSessionInfo(self, userId):
        '''
        加载用户的sessionInfo
        '''
        data = self._redisDao.getConnection(userId).send('hget', self.buildKey(userId), 'session')
        if ttlog.isDebugEnabled():
            ttlog.debug('UserInfoDaoRedis.loadSessionInfo',
                        'userId=', userId,
                        'data=', data)
        if data:
            return strutil.jsonLoads(data)
        return None
    
    def saveSessionInfo(self, userId, sessionInfo):
        '''
        保存用户的sessionInfo
        '''
        data = strutil.jsonDumps(sessionInfo)
        self._redisDao.getConnection(userId).send('hset', self.buildKey(userId), 'session', data)
        if ttlog.isDebugEnabled():
            ttlog.debug('UserInfoDaoRedis.saveSessionInfo',
                        'userId=', userId,
                        'data=', data)


class UserCacheDaoRedis(UserCacheDao):
    def __init__(self, redisDao):
        super(UserCacheDaoRedis, self).__init__()
        self._redisDao = redisDao
    
    @classmethod
    def buildKey(cls, userId):
        return 'user:%s' % (userId)
    
    def saveUser(self, user):
        '''
        保存用户信息到缓存
        '''
        data = strutil.jsonDumps(user.toDict())
        self._redisDao.getConnection(user.userId).send('hset', self.buildKey(user.userId), 'info', data)
        if ttlog.isDebugEnabled():
            ttlog.debug('UserInfoDaoRedis.saveUser',
                       'userId=', user.userId,
                       'data=', data)
            
    def loadUser(self, userId):
        '''
        从缓存加载用户信息
        '''
        data = self._redisDao.getConnection(userId).send('hget', self.buildKey(userId), 'info')
        if ttlog.isDebugEnabled():
            ttlog.debug('UserCacheDaoRedis.loadUser',
                       'userId=', userId,
                       'data=', data)
        if data:
            try:
                data = strutil.jsonLoads(data)
                return User(userId).fromDict(data)
            except:
                ttlog.warn('UserCacheDaoRedis.loadUser BadData',
                           'userId=', userId,
                           'data=', data)
        return None


class RoomCacheDaoRedis(RoomCacheDao):
    def __init__(self, redisDao):
        super(RoomCacheDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room:%s' % (roomId)
    
    def loadRoom(self, roomId):
        '''
        加载房间
        @return: Room/None
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), 'info')
        if data:
            try:
                d = strutil.jsonLoads(data)
                return Room(roomId).fromDict(d)
            except:
                ttlog.warn('RoomCacheDaoRedis.loadRoom BadData',
                           'roomId=', roomId,
                           'data=', data)
        return None
    
    def saveRoom(self, room):
        '''
        保存房间
        '''
        d = room.toDict()
        data = strutil.jsonDumps(d)
        self._redisDao.getConnection(room.roomId).send('hset', self.buildKey(room.roomId), 'info', data)


class RoomStatusDaoRedis(RoomStatusDao):
    def __init__(self, redisDao):
        super(RoomStatusDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room:%s' % (roomId)
    
    def loadRoomStatus(self, roomId):
        '''
        加载房间状态
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), 'status')
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomStatusDaoRedis.loadRoomStatus',
                        'roomId=', roomId,
                        'data=', data)
        if data:
            try:
                d = strutil.jsonLoads(data)
                return RoomStatus().fromDict(d)
            except:
                ttlog.warn('RoomStatusDaoRedis.loadRoomStatus BadData',
                           'roomId=', roomId,
                           'data=', data)
        return None
    
    def saveRoomStatus(self, roomId, roomStatus):
        '''
        保存房间状态
        '''
        data = strutil.jsonDumps(roomStatus.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), 'status', data)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomStatusDaoRedis.saveRoomStatus',
                        'roomId=', roomId,
                        'data=', data)


class RoomMicStatusDaoRedis(RoomMicStatusDao):
    def __init__(self, redisDao):
        super(RoomMicStatusDaoRedis, self).__init__()
        self._redisDao = redisDao
        
    @classmethod
    def buildKey(cls, roomId):
        return 'room_mics:%s' % (roomId)
    
    def loadRoomMicStatusMap(self, roomId):
        '''
        加载房间麦位map
        needInit: 如果mic不存在需要初始化
        '''
        ret = {}
        datas = self._redisDao.getConnection(roomId).send('hgetall', self.buildKey(roomId))
        for i in xrange(len(datas) / 2):
            micId = int(datas[i * 2])
            roomMicStatus = RoomMicStatus(micId)
            data = datas[i * 2 + 1]
            if data:
                try:
                    l = strutil.jsonLoads(data)
                    roomMicStatus.fromDict(l)
                    ret[micId] = roomMicStatus
                except:
                    ttlog.warn('RoomMicStatusDaoRedis.loadRoomMicMap BadData',
                               'roomId=', roomId,
                               'data=', data)
        return ret

    def saveRoomMicStatusMap(self, roomId, roomMicStatusMap):
        '''
        保存房间麦位map
        '''
        gdkv = []
        for roomMicStatus in roomMicStatusMap.values():
            gdkv.append(roomMicStatus.micId)
            gdkv.append(strutil.jsonDumps(roomMicStatus.toDict()))

        self._redisDao.getConnection(roomId).send('hMset', self.buildKey(roomId), *gdkv)

    def loadRoomMicStatus(self, roomId, micId):
        '''
        加载房间麦位
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), micId)
        if data:
            try:
                l = strutil.jsonLoads(data)
                return RoomMicStatus(micId).fromDict(l)
            except:
                ttlog.warn('RoomMicStatusDaoRedis.loadRoomMicMap BadData',
                           'roomId=', roomId,
                           'data=', data)
        return None

    def saveRoomMicStatus(self, roomId, roomMicStatus):
        '''
        保存房间麦位
        '''
        data = strutil.jsonDumps(roomMicStatus.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), roomMicStatus.micId, data)

    def removeRoomAllMicStatus(self, roomId):
        '''
        删除房间麦位
        '''
        self._redisDao.getConnection(roomId).send('del', self.buildKey(roomId))
        
    def removeRoomMicStatus(self, roomId, micId):
        '''
        删除某个麦位
        '''
        self._redisDao.getConnection(roomId).send('hdel', self.buildKey(roomId), micId)


class RoomPKLocationDaoRedis(RoomPKLocationDao):
    def __init__(self, redisDao):
        super(RoomPKLocationDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room_teampk:%s' % (roomId)

    def loadRoomPKLocationMap(self, roomId, locationIds, needInit=True):
        '''
        加载房间麦位map
        needInit: 如果PKLocation不存在需要初始化
        '''
        ret = {}
        datas = self._redisDao.getConnection(roomId).send('hMget', self.buildKey(roomId), *locationIds)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomPKLocationDaoRedis.loadRoomPKLocationMap',
                        'roomId=', roomId,
                        'datas=', datas)
        for i in xrange(len(locationIds)):
            roomPKLocation = RoomPKLocation(locationIds[i])
            data = datas[i]
            if data:
                try:
                    l = strutil.jsonLoads(data)
                    roomPKLocation.fromDict(l)
                except:
                    ttlog.warn('RoomPKLocationDaoRedis.loadRoomPKLocationMap BadData',
                               'roomId=', roomId,
                               'data=', data)
            elif not needInit:
                continue

            ret[roomPKLocation.location] = roomPKLocation
        return ret

    def saveRoomPKLocationMap(self, roomId, roomPKLocationMap):
        '''
        保存房间pk坑位列表
        '''
        gdkv = []
        for roomPKLocation in roomPKLocationMap.values():
            gdkv.append(roomPKLocation.location)
            gdkv.append(strutil.jsonDumps(roomPKLocation.toDict()))

        self._redisDao.getConnection(roomId).send('hMset', self.buildKey(roomId), *gdkv)
        
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomPKLocationDaoRedis.saveRoomPKLocationMap',
                        'roomId=', roomId,
                        'datas=', gdkv)

    def loadRoomPKLocation(self, roomId, locationId):
        '''
        加载房间麦位
        '''
        roomMicStatus = RoomPKLocation(locationId)
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), locationId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomPKLocationDaoRedis.loadRoomPKLocation',
                        'roomId=', roomId,
                        'data=', data)
        if data:
            try:
                l = strutil.jsonLoads(data)
                roomMicStatus.fromDict(l)
            except:
                ttlog.warn('RoomPKLocationDaoRedis.loadRoomPKLocation BadData',
                           'roomId=', roomId,
                           'data=', data)
        return roomMicStatus

    def saveRoomPKLocation(self, roomId, roomPKLocation):
        '''
        保存房间pk坑位
        '''
        data = strutil.jsonDumps(roomPKLocation.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), roomPKLocation.location, data)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomPKLocationDaoRedis.saveRoomPKLocation',
                        'roomId=', roomId,
                        'data=', data)

    def removeRoomAllPKLocation(self, roomId):
        '''
        删除房间pk坑位列表
        '''
        self._redisDao.getConnection(roomId).send('del', self.buildKey(roomId))
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomPKLocationDaoRedis.removeRoomAllPKLocation',
                        'roomId=', roomId)


class RoomTeamPKStatusDaoRedis(RoomTeamPKStatusDao):
    def __init__(self, redisDao):
        super(RoomTeamPKStatusDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room:%s' % (roomId)

    @classmethod
    def buildValueKey(cls):
        return 'teampkinfo'

    def loadRoomTeamPKStatus(self, roomId):
        '''
        加载团战pk
        @return: RoomTeamPKStatus or None
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), self.buildValueKey())
        if data:
            try:
                l = strutil.jsonLoads(data)
                return RoomTeamPKStatus().fromDict(l)
            except:
                ttlog.warn('RoomTeamPKStatusDaoRedis.loadRoomTeamPK BadData',
                           'roomId=', roomId,
                           'data=', data)

        return None

    def saveRoomTeamPKStatus(self, roomId, roomTeamPKStatus):
        '''
        保存团战pk
        '''
        data = strutil.jsonDumps(roomTeamPKStatus.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), self.buildValueKey(), data)

    def removeRoomTeamPKStatus(self, roomId):
        '''
        删除团战pk
        '''
        self._redisDao.getConnection(roomId).send('hdel', self.buildKey(roomId), self.buildValueKey())


class RoomAcrossPKStatusDaoRedis(RoomAcrossPKStatusDao):
    def __init__(self, redisDao):
        super(RoomAcrossPKStatusDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room:%s' % (roomId)

    @classmethod
    def buildValueKey(cls):
        return 'acrosspkinfo'

    def loadRoomAcrossPKStatus(self, roomId):
        '''
        加载跨房pk
        @return: RoomAcrossPKStatus or None
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), self.buildValueKey())
        if data:
            try:
                l = strutil.jsonLoads(data)
                return RoomAcrossPKStatus().fromDict(l)
            except:
                ttlog.warn('RoomAcrossPKStatusDaoRedis.loadRoomAcrossPKStatus BadData',
                           'roomId=', roomId,
                           'data=', data)

        return None

    def saveRoomAcrossPKStatus(self, roomId, roomAcrossPKStatus):
        '''
        保存跨房pk
        '''
        data = strutil.jsonDumps(roomAcrossPKStatus.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), self.buildValueKey(), data)

    def removeRoomAcrossPKStatus(self, roomId):
        '''
        删除跨房pk
        '''
        self._redisDao.getConnection(roomId).send('hdel', self.buildKey(roomId), self.buildValueKey())


class MicUserStatusDaoRedis(MicUserStatusDao):
    def __init__(self, redisDao):
        super(MicUserStatusDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'mic_user_status:%s' % (roomId)

    def loadMicUserStatusMap(self, roomId, userIds):
        '''
        加载房间麦位map
        '''
        ret = {}
        datas = self._redisDao.getConnection(roomId).send('hMget', self.buildKey(roomId), *userIds)
        for data in datas:
            if data:
                micUserStatus = MicUserStatus()
                try:
                    l = strutil.jsonLoads(data)
                    micUserStatus.fromDict(l)
                except:
                    ttlog.warn('MicUserStatusDaoRedis.loadMicUserStatusMap BadData',
                               'roomId=', roomId,
                               'data=', data)
                ret[micUserStatus.userId] = micUserStatus
        return ret

    def saveMicUserStatusMap(self, roomId, micUserStatusMap):
        '''
        保存麦位用户状态map
        '''
        gdkv = []
        for micUserStatus in micUserStatusMap.values():
            gdkv.append(micUserStatus.userId)
            gdkv.append(strutil.jsonDumps(micUserStatus.toDict()))

        self._redisDao.getConnection(roomId).send('hMset', self.buildKey(roomId), *gdkv)
    
    def loadMicUserStatus(self, roomId, userId):
        '''
        加载麦位用户状态
        @return: MicUserStatus or None
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('MicUserStatusDaoRedis.loadMicUserStatus',
                        'roomId=', roomId,
                        'userId=', userId,
                        'data=', data)
        if data:
            try:
                d = strutil.jsonLoads(data)
                return MicUserStatus().fromDict(d)
            except:
                ttlog.warn('MicUserStatusDaoRedis.loadMicUserStatus BadData',
                           'roomId=', roomId,
                           'userId=', userId,
                           'data=', data)
        return None
    
    def saveMicUserStatus(self, roomId, userId, status):
        '''
        保存麦位用户状态
        '''
        data = strutil.jsonDumps(status.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), userId, data)
        if ttlog.isDebugEnabled():
            ttlog.debug('MicUserStatusDaoRedis.saveMicUserStatus',
                        'roomId=', roomId,
                        'userId=', userId,
                        'data=', data)
    
    def removeMicUserStatus(self, roomId, userId):
        '''
        删除麦位用户状态
        '''
        self._redisDao.getConnection(roomId).send('hdel', self.buildKey(roomId), userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('MicUserStatusDaoRedis.removeMicUserStatus',
                        'roomId=', roomId,
                        'userId=', userId)
    

class RoomUserStatusDaoRedis(RoomUserStatusDao):
    def __init__(self, redisDao):
        super(RoomUserStatusDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, roomId):
        return 'room_user_status:%s' % (roomId)
    
    def loadRoomUserStatus(self, roomId, userId):
        '''
        加载房间用户状态
        '''
        data = self._redisDao.getConnection(roomId).send('hget', self.buildKey(roomId), userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomUserStatusDaoRedis.loadRoomUserStatus',
                        'roomId=', roomId,
                        'userId=', userId,
                        'data=', data)
        if data:
            try:
                d = strutil.jsonLoads(data)
                return RoomUserStatus().fromDict(d)
            except:
                ttlog.warn('RoomUserStatusDaoRedis.loadRoomUserStatus BadData',
                           'roomId=', roomId,
                           'userId=', userId,
                           'data=', data)
        return None
    
    def saveRoomUserStatus(self, roomId, userId, status):
        '''
        保存房间用户状态
        '''
        data = strutil.jsonDumps(status.toDict())
        self._redisDao.getConnection(roomId).send('hset', self.buildKey(roomId), userId, data)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomUserStatusDaoRedis.saveRoomUserStatus',
                        'roomId=', roomId,
                        'userId=', userId,
                        'data=', data)

    def removeRoomUserStatus(self, roomId, userId):
        '''
        删除房间用户
        '''
        self._redisDao.getConnection(roomId).send('hdel', self.buildKey(roomId), userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomUserStatusDaoRedis.removeRoomUserStatus',
                        'roomId=', roomId,
                        'userId=', userId)


class RoomServerOnlineUserDaoRedis(RoomServerOnlineUserDao):
    def __init__(self, redisDao):
        super(RoomServerOnlineUserDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, serverId):
        return 'room_server_online_users:%s' % (serverId)
    
    def loadRoomOnlineUsers(self, serverId):
        '''
        加载serverId在线的所有用户
        return list<(userId, roomId)>
        '''
        ret = []
        datas = self._redisDao.getConnection(serverId).send('zrange', self.buildKey(serverId), 0, -1, 'withscores')
        if datas:
                for i in xrange(len(datas) / 2):
                    uidData = datas[i * 2]
                    roomIdData = datas[i * 2 + 1]
                    try:
                        ret.append((int(uidData), int(roomIdData)))
                    except:
                        ttlog.warn('RoomServerOnlineUserDaoRedis.loadRoomOnlineUsers BadData',
                                   'serverId=', serverId,
                                   'data=', (uidData, roomIdData))
        return ret
    
    def addRoomOnlineUser(self, serverId, userId, roomId):
        '''
        添加用户ID
        '''
        self._redisDao.getConnection(serverId).send('zadd', self.buildKey(serverId), roomId, userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomServerOnlineUserDaoRedis.addRoomOnlineUser',
                        'serverId=', serverId,
                        'userId=', userId,
                        'roomId=', roomId)
    
    def removeRoomOnlineUser(self, serverId, userId):
        '''
        删除在线userId
        '''
        self._redisDao.getConnection(serverId).send('zrem', self.buildKey(serverId), userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomServerOnlineUserDaoRedis.removeRoomOnlineUser',
                        'serverId=', serverId,
                        'userId=', userId)


class RoomOnlineUserListDaoRedis(RoomOnlineUserListDao):
    def __init__(self, redisDao):
        super(RoomOnlineUserListDaoRedis, self).__init__()
        self._redisDao = redisDao
    
    @classmethod
    def buildKey(cls, roomId):
        return 'room_online_users:%s' % (roomId)
    
    def setRoomOnlineUser(self, roomId, userId, score):
        '''
        添加用户到roomId所在房间
        '''
        key = self.buildKey(roomId)
        self._redisDao.getConnection(roomId).send('zadd', key, score, userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomOnlineUserListDaoRedis.setRoomOnlineUser',
                        'roomId=', roomId,
                        'userId=', userId,
                        'score=', score)
    
    def removeRoomOnlineUser(self, roomId, userId):
        '''
        删除用户
        '''
        key = self.buildKey(roomId)
        self._redisDao.getConnection(roomId).send('zrem', key, userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomOnlineUserListDaoRedis.removeRoomOnlineUser',
                        'roomId=', roomId,
                        'userId=', userId)
    
    def getRoomOnlineUserIds(self, roomId, pos, count):
        '''
        获取roomId房间pos位置开始count个用户Id
        '''
        assert(count > 0)
        ret = []
        key = self.buildKey(roomId)
        userIdStrList = self._redisDao.getConnection(roomId).send('zrevrange', key, pos, pos + count - 1)
        for userIdStr in userIdStrList:
            try:
                ret.append(int(userIdStr))
            except:
                ttlog.warn('RoomOnlineUserListDaoRedis.getRoomOnlineUserIds BadUserId',
                           'roomId=', roomId,
                           'pos=', pos,
                           'count=', count,
                           'data=', userIdStr)
        return ret
    
    def getRoomOnlineUserCount(self, roomId):
        '''
        获取房间在线用户数量
        '''
        key = self.buildKey(roomId)
        return self._redisDao.getConnection(roomId).send('zcard', key)

    def existsRoomOnlineUser(self, roomId, userId):
        '''
        查询用户是否在线
        '''
        key = self.buildKey(roomId)
        return self._redisDao.getConnection(roomId).send('zscore', key, userId)


class MicServerActiveRoomDaoRedis(MicServerActiveRoomDao):
    def __init__(self, redisDao):
        super(MicServerActiveRoomDaoRedis, self).__init__()
        self._redisDao = redisDao

    @classmethod
    def buildKey(cls, serverId):
        return 'mic_server_active_room:%s' % (serverId)

    def loadActiveRooms(self, serverId):
        '''
        加载serverId活跃的房间
        return list<(roomId)>
        '''
        datas = self._redisDao.getConnection(serverId).send('smembers', self.buildKey(serverId))
        if ttlog.isDebugEnabled():
            ttlog.debug('MicServerActiveRoomDaoRedis.loadActiveRooms',
                        'serverId=', serverId,
                        'datas=', datas)
        return datas

    def addActiveRoom(self, serverId, roomId):
        '''
        添加房间id
        '''
        self._redisDao.getConnection(serverId).send('sadd', self.buildKey(serverId), roomId)
        if ttlog.isDebugEnabled():
            ttlog.debug('MicServerActiveRoomDaoRedis.addActiveRoom',
                        'serverId=', serverId,
                        'roomId=', roomId)

    def removeActiveRoom(self, serverId, roomId):
        '''
        删除活跃的房间Id
        '''
        self._redisDao.getConnection(serverId).send('srem', self.buildKey(serverId), roomId)
        if ttlog.isDebugEnabled():
            ttlog.debug('MicServerActiveRoomDaoRedis.removeActiveRoom',
                        'serverId=', serverId,
                        'roomId=', roomId)
