# -*- coding:utf-8 -*-
'''
Created on 2020年11月6日

@author: zhaojiangang
'''
import time
from fqparty.domain.services.util_service import UtilService
from tomato.utils import ttlog, strutil


class UtilServiceImpl(UtilService):
    def __init__(self, sessionRedisConn, commonRedisConn):
        self._sessionRedisConn = sessionRedisConn
        self._commonRedisConn = commonRedisConn

    def getRoomHeatKey(self, roomId):
        return 'guild_room_hot:%s' % str(roomId)

    def getRoomMicCharms(self, roomId):
        ret = {}
        datas = None
        try:
            datas = self._commonRedisConn.send('hgetall', 'micCharm_%s' % (roomId))
            if datas:
                for i in xrange(len(datas) / 2):
                    ret[int(datas[i * 2])] = int(datas[i * 2 + 1])
        except:
            ttlog.error('UtilServiceImpl::getRoomMicCharms',
                        'roomId=', roomId,
                        'datas=', datas)
        return ret

    def setRoomMicCharm(self, roomId, micId, count):
        self._commonRedisConn.send('hset', 'micCharm_%s' % (roomId), micId, count)

    def getRoomMicCharm(self, roomId, micId):
        return self._commonRedisConn.send('hget', 'micCharm_%s' % (roomId), micId) or 0

    def isKickoutUser(self, roomId, userId):
        return self._commonRedisConn.send('exists', 'room_user_kickout_%s_%s' % (roomId, userId)) == 1

    def isSystemKickoutUser(self, roomId, userId):
        return self._commonRedisConn.send('exists', 'system_room_user_kickout_%s_%s' % (roomId, userId)) == 1

    def isDisabledMsgUser(self, roomId, userId):
        return self._commonRedisConn.send('exists', 'room_user_disable_msg_%s_%s' % (roomId, userId)) == 1

    def isReportDisabledMsgUser(self, userId):
        # 举报处罚禁言
        return self._commonRedisConn.send('exists', 'report_user_disable_msg_%s' % userId)

    def getRoomLockPassword(self, roomId):
        return self._commonRedisConn.send('get', 'room_lock_%s' % (roomId))

    def getUserIdByToken(self, token):
        v = self._sessionRedisConn.send('get', token)
        if ttlog.isDebugEnabled():
            ttlog.debug('UtilServiceImpl.getUserIdByToken',
                        'token=', token,
                        'v=', v)
        try:
            return int(v)
        except:
            return 0

    def getTokenByUserId(self, userId):
        token = self._sessionRedisConn.send('get', userId)
        if ttlog.isDebugEnabled():
            ttlog.debug('UtilServiceImpl.getTokenByUserId',
                        'token=', token,
                        'userId=', userId)
        return token

    def getRoomHeatScore(self, roomId):
        key = self.getRoomHeatKey(roomId)
        memberScore, giftScore, chatScore, orignal = self._commonRedisConn.send('HMGET', key, 'member', 'gift', 'chat',
                                                                                'orignal')
        return int(float(memberScore or 0)) + int(float(giftScore or 0)) + int(float(chatScore or 0)) + int(
            float(orignal or 0))

    def incrRoomChatHeatScore(self, roomId, score, isGuild):
        key = self.getRoomHeatKey(roomId)
        self._commonRedisConn.send('hincrby', key, 'chat', score)

    def clearRoomMemberHeatScore(self, roomId, isGuild):
        key = self.getRoomHeatKey(roomId)
        self._commonRedisConn.send('hset', key, 'member', 0)

    def incrRoomMemberHeatScore(self, roomId, score, isGuild):
        key = self.getRoomHeatKey(roomId)
        ret = self._commonRedisConn.send('hincrby', key, 'member', score)
        if int(ret) < 0:
            self.clearRoomMemberHeatScore(roomId, isGuild)

    def addRoomToRoomList(self, roomId):
        return self._commonRedisConn.send('sadd', 'go_room_list', roomId)

    def removeRoomFromRoomList(self, roomId):
        return self._commonRedisConn.send('srem', 'go_room_list', roomId)

    def addRoomToRoomTypeList(self, roomId, isGuild, roomType):
        key = "online_guild_rooms:%s" if isGuild else "online_person_rooms:%s"
        self._commonRedisConn.send('sadd', key % str(roomType), roomId)

        self._commonRedisConn.send('hset', 'online_rooms_type', str(roomId), roomType)

    def removeRoomFromRoomTypeList(self, roomId, isGuild, roomType):
        key = "online_guild_rooms:%s" if isGuild else "online_person_rooms:%s"
        self._commonRedisConn.send('srem', key % str(roomType), roomId)

        self._commonRedisConn.send('hdel', 'online_rooms_type', str(roomId), roomType)

    def addRoomUser(self, roomId, userId, userName):
        return self._commonRedisConn.send('hset',
                                          'go_room_%s' % (roomId),
                                          userId,
                                          userName)

    def removeRoomUser(self, roomId, userId):
        return self._commonRedisConn.send('hdel',
                                          'go_room_%s' % (roomId),
                                          userId)

    def removeRoom(self, roomId):
        self._commonRedisConn.send('del', 'go_room_%s' % (roomId))

    def addMicUser(self, roomId, micId, userId):
        self._commonRedisConn.send('zadd',
                                   'mic_online_users_%s' % (roomId),
                                   micId,
                                   userId)

    def removeMicUser(self, roomId, userId):
        self._commonRedisConn.send('zrem',
                                   'mic_online_users_%s' % (roomId),
                                   userId)

    def removeAllMicUser(self, roomId):
        self._commonRedisConn.send('del', 'mic_online_users_%s' % (roomId))

    def getCreateAcrossPKs(self):
        ret = {}
        datas = None
        try:
            datas = self._commonRedisConn.send('hgetall', 'create_across_pk')
            if datas:
                for i in xrange(len(datas) / 2):
                    ret[int(datas[i * 2])] = strutil.jsonLoads(datas[i * 2 + 1])
        except:
            ttlog.error('UtilServiceImpl::getCreateAcrossPKs',
                        'datas=', datas)
        return ret

    def setCreateAcrossPK(self, roomId, data):
        self._commonRedisConn.send('hset', 'create_across_pk', roomId, strutil.jsonDumps(data))

    def getCreateAcrossPK(self, roomId):
        data = self._commonRedisConn.send('hget', 'create_across_pk', roomId)
        return strutil.jsonLoads(data) if data else None

    def delCreateAcrossPK(self, roomId):
        self._commonRedisConn.send('hdel', 'create_across_pk', roomId)

    def getAllSponsoredAcrossPK(self, roomId):
        ret = {}
        data = None
        try:
            datas = self._commonRedisConn.send('hgetall', 'sponsored_across_pk:' + str(roomId))
            if datas:
                for i in xrange(len(datas) / 2):
                    ret[int(datas[i * 2])] = strutil.jsonLoads(datas[i * 2 + 1])
        except:
            ttlog.error('UtilServiceImpl::getSponsorAcrossPKs',
                        'data=', data)
        return ret

    def setSponsoredAcrossPK(self, sponsoredRoomId, sponsoreRoomId, data):
        self._commonRedisConn.send('hset', 'sponsored_across_pk:' + str(sponsoredRoomId), sponsoreRoomId,
                                   strutil.jsonDumps(data))

    def getSponsoredAcrossPK(self, sponsoredRoomId, sponsoreRoomId):
        data = self._commonRedisConn.send('hget', 'sponsored_across_pk:' + str(sponsoredRoomId), sponsoreRoomId)
        return strutil.jsonLoads(data) if data else None

    def clearExpireAcrossPK(self, roomId, pkRoomId):
        self._commonRedisConn.send('hdel', 'sponsored_across_pk:' + str(roomId), pkRoomId)

    def clearAcrossPKFinish(self, roomId):
        self._commonRedisConn.send('hdel', 'across_pk_data', roomId)

    def setAcrossPKFinish(self, roomId):
        self._commonRedisConn.send('hset', 'across_pk_data', roomId, 1)

    def getAcrossPKFinish(self, roomId):
        return self._commonRedisConn.send('hget', 'across_pk_data', roomId)

    def getAcrossPKActivity(self, key):
        return self._commonRedisConn.send('hget', 'across_pk_activity', key)

    def getPKOpenConfByKey(self, key):
        return self._commonRedisConn.send('hget', 'pk_open_conf', key)

    def addPKRoomList(self, roomId):
        key = "guild_pk_rooms"
        return self._commonRedisConn.send('sadd', key, roomId)

    def removePKRoomList(self, roomId):
        key = "guild_pk_rooms"
        return self._commonRedisConn.send('srem', key, roomId)

    def addBanRoom(self, roomId):
        key = "ban_rooms"
        return self._commonRedisConn.send('sadd', key, roomId)

    def removeBanRoom(self, roomId):
        key = "ban_rooms"
        return self._commonRedisConn.send('srem', key, roomId)

    def isBannedRoom(self, roomId):
        key = "ban_rooms"
        return self._commonRedisConn.send('sIsMember', key, roomId)

    def getUserPromoteTip(self, userId, roomId):
        key = 'qrcodepromoteuser'
        data = self._commonRedisConn.send('hget', key, userId)
        if data is None:
            return

        try:
            now = int(time.time())
            data = strutil.jsonLoads(data)
            roomIds = data.get('room_id', [])
            if now < int(data.get('expiretime')) and roomId in roomIds:
                return data.get('tip')
        except:
            ttlog.error('UtilServiceImpl.getUserPromoteTip',
                        'data=', data)

    def incrPKOpenNum(self, date, userId):
        self._commonRedisConn.send('hincrby', 'pk_open_user_num_'+date, userId, 1)

    def getPKOpenNum(self, date, userId):
        return self._commonRedisConn.send('hget', 'pk_open_user_num_'+date, userId) or 0
