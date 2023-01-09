# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
import fqparty
from fqparty import dao
from fqparty.dao.api.dao_api import UserDaoApi, RoomDaoApi, AttentionDaoApi
from fqparty.dao.redis.dao_redis import RoomCacheDaoRedis, UserCacheDaoRedis, RoomUserStatusDaoRedis, RoomServerOnlineUserDaoRedis, \
    SessionInfoDaoRedis, MicUserStatusDaoRedis, RoomOnlineUserListDaoRedis, RoomStatusDaoRedis, RoomMicStatusDaoRedis, \
    RoomUserRankDaoRedis, DaoRedis, RoomTeamPKStatusDaoRedis, RoomAcrossPKStatusDaoRedis, RoomPKLocationDaoRedis, EmoticonDaoRedis, \
    RoomLocationDaoRedis
from fqparty.domain.models.attention import AttentionDao
from fqparty.domain.models.emoticon import EmoticonDao
from fqparty.domain.models.location import RoomLocationDao
from fqparty.domain.models.room import RoomUserStatusDao, MicUserStatusDao, RoomMicStatusDao, RoomStatusDao, RoomDao, RoomUserRankDao
from fqparty.domain.models.user import UserCacheDao, UserDao, SessionInfoDao
from fqparty.domain.room.room import ActiveRoomManager, RoomUserManager, ActiveRoomManagerImpl, RoomUserManagerImpl, \
    RoomServerOnlineUserDao, RoomUser, RoomOnlineUserListDao, RoomUserInfoLoader, RoomUserInfoLoaderImpl
from fqparty.domain.mic.room_team_pk import RoomTeamPKStatusDao, RoomPKLocationDao
from fqparty.domain.mic.room_across_pk import RoomAcrossPKStatusDao
from fqparty.domain.services.room_service import RoomService
from fqparty.domain.events.room_utils_handler import RoomUtilsHandler
from fqparty.domain.events.room_online_handler import RoomOnlineHandler
import tomato
from tomato.utils import ttlog


class RoomServer(object):
    userDao = UserDao()
    userCacheDao = UserCacheDao()
    sessionInfoDao = SessionInfoDao()
    roomServerOnlineUserDao = RoomServerOnlineUserDao()

    confDao = EmoticonDao()
    attentionDao = AttentionDao()

    roomDao = RoomDao()
    roomStatusDao = RoomStatusDao()
    roomMicStatusDao = RoomMicStatusDao()
    
    roomUserStatusDao = RoomUserStatusDao()
    micUserStatusDao = MicUserStatusDao()
    activeRoomManager = ActiveRoomManager()
    roomUserManager = RoomUserManager()
    roomOnlineUserListDao = RoomOnlineUserListDao()
    roomLocationDao = RoomLocationDao()
    roomTeamPKStatusDao = RoomTeamPKStatusDao()
    roomPKLocationDao = RoomPKLocationDao()
    roomAcrossPKStatusDao = RoomAcrossPKStatusDao()
    
    roomUserRankDao = RoomUserRankDao()
    roomUserInfoLoader = RoomUserInfoLoader()
    
    roomService = RoomService()

    roomOnlineHandler = None
    roomUtilsHandler = None
    roomProto = None
    
    @classmethod
    def getDayConsume(cls, roomId, userId):
        dayConsume = cls.roomUserRankDao.getRoomRickDayValue(userId, roomId)
        return int(dayConsume) if dayConsume else 0


def initServer():
    from fqparty.domain.events.room_proto import RoomProto
    from fqparty.domain.services.impl.room_service_impl import RoomServiceImpl

    ttlog.info('room.initServer')
    
    # connections = dao.getMysqlConns('user')
    # attentionDao = AttentionDaoMysql(connections)
    # roomTypeDao = RoomTypeDaoMysql(connections)
    # roomAdminDao = RoomAdminDaoMysql(connections)
    # roomDao = RoomDaoMysql(connections, roomAdminDao, roomTypeDao)

    attentionDao = AttentionDaoApi()
    userDao = UserDaoApi()
    roomDao = RoomDaoApi()
    
    userRedisDao = DaoRedis(dao.getRedisConns('users'))
    roomRedisDao = DaoRedis(dao.getRedisConns('rooms'))
    rankDaoRedis = DaoRedis(dao.getRedisConns('ranking'))
    configRedisDao = DaoRedis(dao.getRedisConns('config'))

    RoomServer.roomDao = roomDao
    RoomServer.userDao = userDao
    RoomServer.attentionDao = attentionDao
    RoomServer.confDao = EmoticonDaoRedis(configRedisDao)
    RoomServer.userCacheDao = UserCacheDaoRedis(userRedisDao)
    RoomServer.sessionInfoDao = SessionInfoDaoRedis(userRedisDao)
    
    RoomServer.roomStatusDao = RoomStatusDaoRedis(roomRedisDao)
    RoomServer.roomMicStatusDao = RoomMicStatusDaoRedis(roomRedisDao)
    
    RoomServer.roomUserStatusDao = RoomUserStatusDaoRedis(roomRedisDao)
    RoomServer.micUserStatusDao = MicUserStatusDaoRedis(roomRedisDao)
    RoomServer.roomServerOnlineUserDao = RoomServerOnlineUserDaoRedis(roomRedisDao)
    RoomServer.roomOnlineUserListDao = RoomOnlineUserListDaoRedis(roomRedisDao)
    RoomServer.roomLocationDao = RoomLocationDaoRedis(DaoRedis(dao.getRedisConns('common')))
    RoomServer.roomTeamPKStatusDao = RoomTeamPKStatusDaoRedis(roomRedisDao)
    RoomServer.roomPKLocationDao = RoomPKLocationDaoRedis(roomRedisDao)
    RoomServer.roomAcrossPKStatusDao = RoomAcrossPKStatusDaoRedis(roomRedisDao)
    
    RoomServer.roomUserRankDao = RoomUserRankDaoRedis(rankDaoRedis)
    
    RoomServer.roomUserInfoLoader = RoomUserInfoLoaderImpl(RoomServer.userCacheDao, RoomServer.sessionInfoDao, RoomServer.roomUserStatusDao,
                                                           RoomServer.micUserStatusDao, RoomServer.roomMicStatusDao)
    RoomServer.activeRoomManager = ActiveRoomManagerImpl(roomDao, userDao)
    RoomServer.roomUserManager = RoomUserManagerImpl()
    RoomServer.roomService = RoomServiceImpl()
    RoomServer.roomProto = RoomProto()
    RoomServer.roomUtilsHandler = RoomUtilsHandler()


def _loadRoomUser(userId, roomId):
    user = RoomServer.userCacheDao.loadUser(userId)
    if user:
        status = RoomServer.roomUserStatusDao.loadRoomUserStatus(roomId, userId)
        if status:
            sessionInfo = RoomServer.sessionInfoDao.loadSessionInfo(userId)
            if sessionInfo:
                dayConsume = RoomServer.getDayConsume(roomId, userId)
                return RoomUser(roomId, user, status, sessionInfo, dayConsume)
    return None


def _loadRoomServer(isReload=True):
    ttlog.info('>>> room._loadRoomServer',
               'isReload=', isReload)
    
    onlineUsers = RoomServer.roomServerOnlineUserDao.loadRoomOnlineUsers(tomato.app.serverId)
    for userId, roomId in onlineUsers:
        if isReload:
            roomUser = _loadRoomUser(userId, roomId)
            if not roomUser:
                RoomServer.roomServerOnlineUserDao.removeRoomOnlineUser(tomato.app.serverId, userId)
                RoomServer.roomOnlineUserListDao.removeRoomOnlineUser(roomId, userId)
                fqparty.app.utilService.removeRoomUser(roomId, userId)
            else:
                RoomServer.roomUserManager.addRoomUser(roomUser)
        else:
            # 不load重启要删除用户的loc
            RoomServer.roomLocationDao.removeRoomLocation(userId)
            RoomServer.roomServerOnlineUserDao.removeRoomOnlineUser(tomato.app.serverId, userId)
            RoomServer.roomOnlineUserListDao.removeRoomOnlineUser(roomId, userId)
            RoomServer.roomUserStatusDao.removeRoomUserStatus(roomId, userId)
            RoomServer.micUserStatusDao.removeMicUserStatus(roomId, userId)
            fqparty.app.utilService.removeRoomUser(roomId, userId)

    roomUserIdSet = RoomServer.roomUserManager.getRoomIdUserSet()
    for roomId in roomUserIdSet:
        try:
            RoomServer.activeRoomManager.findOrLoadActiveRoom(roomId, None)
        except:
            ttlog.warn('room._loadRoomServer',
                       'roomId=', roomId,
                       'err=', 'NotFoundRoom')
    
    activeRoomMap = RoomServer.activeRoomManager.getActiveRoomMap()
    ttlog.info('<<< room._loadRoomServer',
               'isReload=', isReload,
               'onlineUsers=', onlineUsers,
               'activeRooms=', activeRoomMap.keys())

def startServer():
    serverId = tomato.app.serverId
    
    ttlog.info('>>> room.startServer serverId=', serverId)
    RoomServer.roomUtilsHandler.setupEvents()
    RoomServer.roomOnlineHandler = RoomOnlineHandler()
    
    isReload = tomato.app.appArgs and tomato.app.appArgs[0] == '1'
    _loadRoomServer(isReload)
    
    RoomServer.roomProto.setupEvents()
    
    ttlog.info('<<< room.startServer serverId=', serverId)



