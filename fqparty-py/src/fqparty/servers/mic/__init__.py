# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty import dao
import fqparty
from fqparty.dao.api.dao_api import UserDaoApi, RoomDaoApi
from fqparty.dao.mysql.dao_mysql import RoomDaoMysql, RoomAdminDaoMysql, \
    RoomTypeDaoMysql, PKDaoMysql
from fqparty.dao.redis.dao_redis import EmoticonDaoRedis, UserCacheDaoRedis, \
    MicUserStatusDaoRedis, RoomOnlineUserListDaoRedis, RoomStatusDaoRedis, \
    RoomMicStatusDaoRedis, DaoRedis, RoomPKLocationDaoRedis, \
    RoomTeamPKStatusDaoRedis, MicServerActiveRoomDaoRedis, \
    RoomAcrossPKStatusDaoRedis, SessionInfoDaoRedis
from fqparty.dao.mq.dao_mq import DaoMq
from fqparty.domain.mic.room_across_pk import RoomAcrossPKStatusDao
from fqparty.domain.mic.room_manager import ActiveMicManager
from fqparty.domain.mic.room_team_pk import RoomTeamPKStatusDao, RoomPKLocationDao
from fqparty.domain.models.emoticon import EmoticonDao
from fqparty.domain.models.room import MicUserStatusDao, RoomMicStatusDao, RoomStatusDao, RoomDao
from fqparty.domain.models.user import UserCacheDao, UserDao, SessionInfoDao
from fqparty.domain.room.room import RoomOnlineUserListDao, MicServerActiveRoomDao
from fqparty.domain.services.mic_room_service import MicRoomService
import tomato
from tomato.utils import ttlog


class MicServer(object):
    pkDao = UserDao()
    roomDao = RoomDao()
    confDao = EmoticonDao()
    userDao = UserDao()
    userCacheDao = UserCacheDao()
    sessionInfoDao = SessionInfoDao()
    roomStatusDao = RoomStatusDao()
    roomMicStatusDao = RoomMicStatusDao()
    roomPKLocationDao = RoomPKLocationDao()
    micUserStatusDao = MicUserStatusDao()
    roomTeamPKStatusDao = RoomTeamPKStatusDao()
    roomAcrossPKStatusDao = RoomAcrossPKStatusDao()
    roomOnlineUserListDao = RoomOnlineUserListDao()
    micServerActiveRoomDao = MicServerActiveRoomDao()

    activeRoomManager = ActiveMicManager()
    micRoomService = MicRoomService()
    roomUtilsHandler = None
    micProto = None

    @classmethod
    def existsOnlineUser(cls, roomId, userId):
        '''
        用户是否在线
        '''
        status = cls.micUserStatusDao.loadMicUserStatus(roomId, userId)
        return True if status else False


def initServer():
    from fqparty.domain.events.mic_utils_handler import MicUtilsHandler
    from fqparty.domain.events.mic_proto import MicProto
    from fqparty.domain.services.impl.mic_room_service_impl import MicRoomServiceImpl
    from fqparty.domain.mic.room import ActiveMicManagerImpl
    
    ttlog.info('mic.initServer')
    connections = dao.getMysqlConns('user')
    # roomTypeDao = RoomTypeDaoMysql(connections)
    # roomAdminDao = RoomAdminDaoMysql(connections)
    # roomDao = RoomDaoMysql(connections, roomAdminDao, roomTypeDao)
    userDao = UserDaoApi()
    roomDao = RoomDaoApi()

    userRedisDao = DaoRedis(dao.getRedisConns('users'))
    roomRedisDao = DaoRedis(dao.getRedisConns('rooms'))
    configRedisDao = DaoRedis(dao.getRedisConns('config'))
    confDao = EmoticonDaoRedis(configRedisDao)
    pkDao = PKDaoMysql(connections)

    MicServer.pkDao = pkDao
    MicServer.confDao = confDao
    MicServer.roomDao = roomDao
    MicServer.userDao = userDao
    # MicServer.micMq = DaoMq(dao.getMqChannelConf('mic'))
    MicServer.userCacheDao = UserCacheDaoRedis(userRedisDao)
    MicServer.sessionInfoDao = SessionInfoDaoRedis(userRedisDao)
    MicServer.roomStatusDao = RoomStatusDaoRedis(roomRedisDao)
    MicServer.roomMicStatusDao = RoomMicStatusDaoRedis(roomRedisDao)
    MicServer.roomPKLocationDao = RoomPKLocationDaoRedis(roomRedisDao)
    MicServer.micUserStatusDao = MicUserStatusDaoRedis(roomRedisDao)
    MicServer.roomTeamPKStatusDao = RoomTeamPKStatusDaoRedis(roomRedisDao)
    MicServer.roomAcrossPKStatusDao = RoomAcrossPKStatusDaoRedis(roomRedisDao)
    MicServer.roomOnlineUserListDao = RoomOnlineUserListDaoRedis(roomRedisDao)
    MicServer.micServerActiveRoomDao = MicServerActiveRoomDaoRedis(roomRedisDao)

    MicServer.activeRoomManager = ActiveMicManagerImpl()
    MicServer.roomUtilsHandler = MicUtilsHandler()
    MicServer.micProto = MicProto()
    MicServer.micRoomService = MicRoomServiceImpl()

# 
# def _updateMicUserStatusMap(roomId):
#     '''更新麦位、pk位、用户麦上状态'''
#     needUpdatMicUserMap = {}
# 
#     # 更新麦位
#     needRoomMicStatusMap = {}
#     roomMicStatusMap = MicServer.roomMicStatusDao.loadRoomMicStatusMap(roomId, MicIds.micIDs, False)
#     for roomMicStatus in roomMicStatusMap.values():
#         if roomMicStatus.userId:
#             needUpdatMicUserMap[roomMicStatus.userId] = 1
#             roomMicStatus.userId = 0
#             needRoomMicStatusMap[roomMicStatus.micId] = roomMicStatus
# 
#     if needRoomMicStatusMap:
#         MicServer.roomMicStatusDao.saveRoomMicStatusMap(roomId, needRoomMicStatusMap)
# 
#     # 更新pk位
#     needRoomPKLocationMap = {}
#     roomPKLocationMap = MicServer.roomPKLocationDao.loadRoomPKLocationMap(roomId, MicIds.pkIDs, False)
#     for roomPKLocation in roomPKLocationMap.values():
#         if roomPKLocation.userId:
#             needUpdatMicUserMap[roomPKLocation.userId] = 1
#             roomPKLocation.userId = 0
#             roomPKLocation.micId = 0
#             needRoomPKLocationMap[roomPKLocation.location] = roomPKLocation
# 
#     if needRoomPKLocationMap:
#         MicServer.roomPKLocationDao.saveRoomPKLocationMap(roomId, needRoomPKLocationMap)
# 
#     needMicUserStatusMap = {}
#     if needUpdatMicUserMap:
#         micUserStatusMap = MicServer.micUserStatusDao.loadMicUserStatusMap(roomId, needUpdatMicUserMap.keys())
#         for micUserStatus in micUserStatusMap.values():
#             if micUserStatus.micId or micUserStatus.pkLoactionId:
#                 micUserStatus.micId = 0
#                 micUserStatus.pkLoactionId = 0
#                 needMicUserStatusMap[micUserStatus.userId] = micUserStatus
# 
#         if needMicUserStatusMap:
#             MicServer.micUserStatusDao.saveMicUserStatusMap(roomId, needMicUserStatusMap)
# 
#     ttlog.info('mic._updateMicUserStatusMap',
#                'roomId=', roomId,
#                'needRoomMicStatusMap=', needRoomMicStatusMap.keys(),
#                'needRoomPKLocationMap=', needRoomPKLocationMap.keys(),
#                'needUpdatMicUserMap=', needUpdatMicUserMap.keys(),
#                'needMicUserStatusMap=', needMicUserStatusMap.keys())

def _loadRoomServer(isReload=True):
    ttlog.info('>>> mic._loadRoomServer',
               'isReload=', isReload)

    activeRooms = MicServer.micServerActiveRoomDao.loadActiveRooms(tomato.app.serverId)
    for roomId in activeRooms:
        if isReload:
            roomId = int(roomId)
            try:
                micRoom = MicServer.activeRoomManager.findOrLoadActiveRoom(roomId, None)
            except Exception, e:
                ttlog.warn('mic._loadRoomServer',
                           'roomId=', roomId,
                           'err=', 'NotFoundRoom',
                           'ex=', e)
        else:
            MicServer.micServerActiveRoomDao.removeActiveRoom(tomato.app.serverId, roomId)
            MicServer.roomMicStatusDao.removeRoomAllMicStatus(roomId)
            MicServer.roomPKLocationDao.removeRoomAllPKLocation(roomId)
            MicServer.roomTeamPKStatusDao.removeRoomTeamPKStatus(roomId)
            MicServer.roomAcrossPKStatusDao.removeRoomAcrossPKStatus(roomId)
            fqparty.app.utilService.removeAllMicUser(roomId)
            fqparty.app.utilService.removePKRoomList(roomId)
            fqparty.app.utilService.removeRoomFromRoomList(roomId)

    micRoomMap = MicServer.activeRoomManager.getActiveRoomMap()
    for _, micRoom in micRoomMap.iteritems():
        micRoom._initLoad()
    
    ttlog.info('<<< mic._loadRoomServer',
               'isReload=', isReload,
               'micRoomIds=', micRoomMap.keys())


def startServer():
    serverId = tomato.app.serverId

    ttlog.info('>>> mic.startServer serverId=', serverId)
    MicServer.roomUtilsHandler.setupEvents()

    isReload = tomato.app.appArgs and tomato.app.appArgs[0] == '1'
    _loadRoomServer(isReload)

    MicServer.micProto.setupEvents()
    
    micRoomMap = MicServer.activeRoomManager.getActiveRoomMap()
    for _, micRoom in micRoomMap.iteritems():
        micRoom.start()
    
    ttlog.info('<<< mic.startServer serverId=', serverId)


