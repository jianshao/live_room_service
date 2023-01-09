# -*- coding:utf-8 -*-
'''
Created on 2021年3月9日

@author: zhaojiangang
'''
from fqparty.domain.models.user import UserDao, User, UserAttire, UserWoreAttire
from fqparty.domain.models.room import RoomDao, Room, RoomAdmin, RoomType
from fqparty.domain.models.attention import AttentionDao, Attention
from fqparty.utils import phpapi
from tomato.utils import ttlog, timeutil


TRANS_MAP = {
    'bubble': 48,
    'avatar': 1,
    'voiceprint':101,
    'mount':103
}

def propType2Pid(propType):
    return TRANS_MAP.get(propType, 0)


class UserDaoApi(UserDao):
    def __init__(self):
        super(UserDaoApi, self).__init__()

    def loadUser(self, userId):
        ec, userInfo = phpapi.queryUserInfoForRoom(userId)
        
        if ttlog.isDebugEnabled():
            ttlog.debug('UserDaoApi.loadUser',
                        'userId=', userId,
                        'ec=', ec,
                        'userInfo=', userInfo)
        if ec != 0:
            return None

        profile = userInfo['profile']
        props = userInfo.get('props', [])
        waredProps = userInfo.get('waredProps', [])
        
        ret = User(userId)
        ret.auditProfile = userInfo.get('auditProfile', {})
        ret.userName = profile['username']
        ret.password = profile['password']
        ret.nickname = profile['nickname']
        ret.sex = profile['sex']
        ret.isVip = profile['vipLevel']
        ret.role = profile['role']
        ret.userLevel = profile['level']
        ret.avatar = profile['avatar']
        ret.prettyId = profile['prettyId']
        ret.prettyAvatar = profile['prettyAvatar']
        ret.prettyAvatarSvga = profile['prettyAvatarSvga']
        ret.dukeId = profile['dukeId']
        ret.attestation = profile.get('attestation', 0)
        ret.registerTime = profile.get('registerTime', 0)
        ret.guildInfo = userInfo.get('userGuildInfo', {})
        ret.attires = [UserAttire(prop['propId'], prop['isWore']) for prop in props]
        ret.woreAttires = self._decodeWaredAttires(waredProps)
        for wa in ret.woreAttires:
            if wa.attrType == 'bubble':
                # 气泡框和爵位气泡框
                ret.bubbleIos = wa.imageIos
                ret.bubbleAndroid = wa.imageAndroid
        return ret
    
    def _decodeWaredAttires(self, waredProps):
        ret = []
        for waredProp in waredProps:
            wa = UserWoreAttire()
            wa.kindId = waredProp.get('kindId')
            wa.attrId = waredProp['propId']
            wa.attrPid = propType2Pid(waredProp['type'])
            wa.attrType = waredProp['type']
            wa.imageAndroid = waredProp['imageAndroid']
            wa.imageIos = waredProp['imageIos']
            wa.svga = waredProp['animation']
            wa.color = waredProp['color']
            wa.multiple = waredProp['multiple']
            ret.append(wa)
        return ret


class RoomDaoApi(RoomDao):
    def __init__(self):
        super(RoomDaoApi, self).__init__()

    def loadRoom(self, roomId):
        ec, roomInfo = phpapi.queryRoomInfoForRoom(roomId)

        if ttlog.isDebugEnabled():
            ttlog.debug('RoomDaoApi.loadRoom',
                        'roomId=', roomId,
                        'ec=', ec,
                        'roomInfo=', roomInfo)
        if ec != 0:
            return None

        room = Room(roomId)
        room.roomName = roomInfo['roomName']
        room.ownerUserId = roomInfo['ownerUserId']
        room.password = roomInfo['password']
        room.isWheat = roomInfo['isWheat']
        room.roomDesc = roomInfo['roomDesc']
        room.roomWelcomes = roomInfo['roomWelcomes']
        room.backgroundImage = roomInfo['backgroundImage']
        room.guildId = roomInfo['guildId']
        room.createTime = roomInfo['createTime']
        room.roomLock = roomInfo['roomLock']
        room.prettyRoomId = roomInfo['prettyRoomId']
        room.roomType = self._decodeRoomType(roomInfo['roomTypeInfo'])
        room.adminMap = self._decodeRoomAdmins(roomInfo['managerList'])

        return room

    def searchRoom(self, searchId):
        ec, roomInfo = phpapi.searchRoomInfoForRoom(searchId)

        if ttlog.isDebugEnabled():
            ttlog.debug('RoomDaoApi.loadRoom',
                        'searchId=', searchId,
                        'ec=', ec,
                        'roomInfo=', roomInfo)
        if ec != 0:
            return None

        room = Room(roomInfo['roomId'])
        room.roomName = roomInfo['roomName']
        room.ownerUserId = roomInfo['ownerUserId']
        room.password = roomInfo['password']
        room.isWheat = roomInfo['isWheat']
        room.roomDesc = roomInfo['roomDesc']
        room.roomWelcomes = roomInfo['roomWelcomes']
        room.backgroundImage = roomInfo['backgroundImage']
        room.guildId = roomInfo['guildId']
        room.createTime = roomInfo['createTime']
        room.roomLock = roomInfo['roomLock']
        room.prettyRoomId = roomInfo['prettyRoomId']
        room.roomType = self._decodeRoomType(roomInfo['roomTypeInfo'])
        room.adminMap = self._decodeRoomAdmins(roomInfo['managerList'])

        return room

    def _decodeRoomType(self, roomTypeInfo):
        roomType = RoomType(roomTypeInfo['typeId'])
        roomType.parentId = roomTypeInfo['parentId']
        roomType.modeName = roomTypeInfo['modeName']
        roomType.createTime = roomTypeInfo['createTime']
        roomType.modeType = roomTypeInfo['modeType']
        roomType.status = roomTypeInfo['status']
        return roomType

    def _decodeRoomAdmins(self, managerList):
        ret = {}
        for manager in managerList:
            ra = RoomAdmin()
            ra.userId = manager['userId']
            ra.adminType = manager['adminType']
            ret[ra.userId] = ra
        return ret


class AttentionDaoApi(AttentionDao):
    def __init__(self):
        super(AttentionDaoApi, self).__init__()

    def loadAttention(self, userId, userIdEd):
        ec, attentionInfo = phpapi.queryAttentionForRoom(userId, userIdEd)

        if ttlog.isDebugEnabled():
            ttlog.debug('RoomDaoApi.loadRoom',
                        'userId=', userId,
                        'userIdEd=', userIdEd,
                        'ec=', ec,
                        'attentionInfo=', attentionInfo)
        if ec != 0:
            return None

        ret = Attention()
        ret.userId = attentionInfo['userId']
        ret.userIdEd = attentionInfo['attentionId']
        ret.attentionTime = attentionInfo['createTime']

        return ret



