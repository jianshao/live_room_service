# -*- coding:utf-8 -*-
'''
Created on 2020年10月27日

@author: zhaojiangang
'''
import binascii

from fqparty.const import AdminTypes
from fqparty.domain.models.attention import AttentionDao, Attention
from fqparty.domain.models.room import RoomDao, RoomTypeDao, Room, RoomAdmin, \
    RoomAdminDao, RoomType
from fqparty.domain.models.user import UserDao
from tomato.utils import timeutil


class DaoMysql(object):
    def __init__(self, connections):
        self._connections = connections if isinstance(connections, list) else [connections]

    def _getConnection(self, key):
        index = 0
        if len(self._connections) > 1:
            if isinstance(key, int):
                index = len(self._connections) % key
            else:
                index = binascii.crc32('%s' % (key)) % len(self._connections)
        return self._connections[index]


class AttentionDaoMysql(DaoMysql, AttentionDao):
    def __init__(self, connections):
        super(AttentionDaoMysql, self).__init__(connections)
        
    def loadAttention(self, userId, userIdEd):
        res = self._getConnection(userId).runQuery('select `userided`, `type`, `attention_time` \
                                                from `zb_attention` where userid=%s and userided=%s', (userId, userIdEd))
        if not res or not res[0]:
            return None
        
        res = res[0]
        ret = Attention()
        ret.userId = userId
        ret.userIdEd = res[0]
        ret.atype = res[1]
        ret.attentionTime = timeutil.datetimeToTimestamp(res[2])

        if ret.atype == 1:
            return None

        return ret


class RoomTypeDaoMysql(DaoMysql, RoomTypeDao):
    def __init__(self, connections):
        super(RoomTypeDaoMysql, self).__init__(connections)

    def loadRoomType(self, typeId):
        res = self._getConnection(typeId).runQuery('select `pid`, `room_mode`, `creat_time`, \
                                                    `mode_type`, `status` from `zb_room_mode` \
                                                    where id=%s', (typeId))
        if not res or not res[0]:
            return None

        res = res[0]
        
        roomType = RoomType(typeId)
        roomType.parentId = res[0]
        roomType.modeName = res[1]
        roomType.createTime = res[2]
        roomType.modeType = res[3]
        roomType.status = res[4]
        return roomType


class RoomAdminDaoMysql(DaoMysql, RoomAdminDao):
    def __init__(self, connections):
        super(RoomAdminDaoMysql, self).__init__(connections)

    def loadRoomAdmins(self, roomId):
        '''
        加载所有admin
        @return: list<RoomAdmin>
        '''
        ret = []
        res = self._getConnection(roomId).runQuery('select `user_id`, `type`, `creattime` \
                                        from `zb_room_manager` where rooms_id=%s', (roomId))
        
        if res:
            for data in res:
                ra = RoomAdmin()
                ra.userId = data[0]
                if data[1] == 0:
                    ra.adminType = AdminTypes.ADMIN
                elif data[1] == 1:
                    ra.adminType = AdminTypes.OWNER
                elif data[1] == 2:
                    ra.adminType = AdminTypes.SUPER
                else:
                    ra.adminType = 0
                # ra.createDT = timeutil.datetimeToTimestamp(data[2])
                ret.append(ra)
        return ret


class RoomDaoMysql(DaoMysql, RoomDao):
    def __init__(self, connections, roomAdminDao, roomTypeDao):
        super(RoomDaoMysql, self).__init__(connections)
        self._roomAdminDao = roomAdminDao
        self._roomTypeDao = roomTypeDao

    def loadRoom(self, roomId):
        res = self._getConnection(roomId).runQuery('select `id`, `room_name`, `room_type`, `user_id`, \
                                    `room_password`, `is_wheat`, `room_desc`, \
                                    `room_welcomes`, `background_image`, \
                                    `guild_id`, `room_createtime`, `room_lock`, `is_wheat`, `pretty_room_id` \
                                    from `zb_languageroom` where id=%s or pretty_room_id=%s', (roomId, roomId))
        if not res or not res[0]:
            return None

        res = res[0]
        ret = Room(res[0])
        ret.roomName = res[1]
        ret.roomType = res[2]
        ret.ownerUserId = res[3]
        ret.password = res[4]
        ret.isWheat = res[5]
        ret.roomDesc = res[6]
        ret.roomWelcomes = res[7]
        ret.backgroundImage = res[8]
        ret.guildId = res[9]
        ret.createTime = res[10]
        ret.roomLock = res[11]
        ret.isWheat = res[12]
        ret.prettyRoomId = res[13]
        ret.roomType = self._roomTypeDao.loadRoomType(res[2])
        roomAdmins = self._roomAdminDao.loadRoomAdmins(roomId)
        ret.adminMap = {ra.userId:ra for ra in roomAdmins}
        return ret


class PKDaoMysql(DaoMysql, UserDao):
    def __init__(self, connections):
        super(PKDaoMysql, self).__init__(connections)

    def addPK(self, redRoomId, blueRoomId, pkMode, createTime, endTime, punishment, winPK, redPKData, redContributeData,
              bluePKData, blueContributeData):
        sqlstr = 'INSERT ignore INTO zb_room_pk (red_room_id, blue_room_id, pk_mode, create_time, end_time, punishment, ' \
                 'win_team, red_pk_data, red_contribute_data, blue_pk_data, blue_contribute_data) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        self._getConnection(redRoomId).runQuery(sqlstr, (redRoomId, blueRoomId, pkMode, createTime, endTime,
            punishment, winPK, redPKData, redContributeData, bluePKData, blueContributeData))
