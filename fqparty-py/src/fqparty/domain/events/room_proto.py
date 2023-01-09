# -*- coding:utf-8 -*-
'''
Created on 2022年2月4日

@author: zhaojiangang
'''
import math
import time
from datetime import datetime
from sre_compile import isstring

import fqparty
from fqparty.const import UserLeaveRoomReason, MicIds
from fqparty.domain.events.events import UserEnterRoomEvent, UserReconnectRoomEvent, UserLeaveRoomEvent, SendTextMsgToRoomEvent, \
    PushRoomUserListThreeEvent, PushRoomInfoEvent, PushRoomUserInfoEvent, PushRoomUserListAllEvent, PushRoomUserListEvent, \
    LockRoomEvent, SendRoomMsgEvent, SendRoomMsgToUserEvent, PushRoomMsgEvent, PushRoomLedMsgEvent, DisabledUserMsgEvent, \
    RoomUserUpdateEvent
from fqparty.domain.models.room import RoomStatus, PKMode, RoomMicStatus
from fqparty.proxy.room import room_remote_proxy
from fqparty.servers.room import RoomServer
from fqparty.utils import proto_utils
import tomato
from tomato.common.proxy import session_remote_proxy
from tomato.utils import strutil, ttlog
from fqparty.domain.room.room import RoomMicInfo, RoomTeamPKInfo, RoomAcrossPKInfo
from fqparty.domain.events.black_industry import BlackIndustryStrategy, FILTER_PROTECT_USER, FILTER_HEICHAN_USER


def _getValidUserIds(userId, roomId, start, count):
    userIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(roomId, 0, 999999)
    # 根据防黑产策略过滤掉受保护的用户
    blockInfo = BlackIndustryStrategy(userId, userIds, FILTER_PROTECT_USER)
    userIds = blockInfo.afterFilter()
    return userIds[start: count + start], len(userIds)


class RoomProto(object):
    def setupEvents(self):
        fqparty.app.on(UserEnterRoomEvent, self._onUserEnterRoomEvent)
        fqparty.app.on(UserReconnectRoomEvent, self._onUserReconnectRoomEvent)
        fqparty.app.on(UserLeaveRoomEvent, self._onUserLeaveRoomEvent)
        fqparty.app.on(SendTextMsgToRoomEvent, self._onSendTextMsgToRoomEvent)
        fqparty.app.on(PushRoomInfoEvent, self._onPushRoomInfoEvent)
        fqparty.app.on(LockRoomEvent, self._onLockRoomEvent)
        fqparty.app.on(PushRoomUserInfoEvent, self._onPushRoomUserInfoEvent)
        fqparty.app.on(PushRoomUserListEvent, self._onPushRoomUserListEvent)
        fqparty.app.on(PushRoomUserListAllEvent, self._onPushRoomUserListAllEvent)
        fqparty.app.on(PushRoomUserListThreeEvent, self._onPushRoomUserListThreeEvent)
        fqparty.app.on(SendRoomMsgEvent, self._onSendRoomMsgEvent)
        fqparty.app.on(SendRoomMsgToUserEvent, self._onSendRoomMsgToUserEvent)
        fqparty.app.on(PushRoomMsgEvent, self._onPushRoomMsgEvent)
        fqparty.app.on(PushRoomLedMsgEvent, self._onPushRoomLedMsgEvent)
        fqparty.app.on(DisabledUserMsgEvent, self._onDisabledUserMsgEvent)
        fqparty.app.on(RoomUserUpdateEvent, self._onRoomUserUpdateEvent)

    @classmethod
    def _buildUserEnterRoomMsgOld(self, activeRoom, roomUser):
        tip = fqparty.app.utilService.getUserPromoteTip(roomUser.userId, activeRoom.roomId) or ''
        totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(activeRoom.roomId)
        heartValue = fqparty.app.utilService.getRoomHeatScore(activeRoom.roomId)
        return {
            'op': 1001,
            'msgId': 1001,
            'roomId': activeRoom.roomId,
            'userId': roomUser.userId,
            'userLevel': roomUser.user.userLevel,
            'userName': roomUser.user.nickname,
            'sex': roomUser.user.sex,
            'headImageUrl': proto_utils.buildImageUrl(roomUser.user.avatar),
            'isVip': roomUser.user.isVip,
            'prettyId': roomUser.user.prettyId,
            'isNewUser': roomUser.user.isNewUser,
            'userIdentity': activeRoom.getUserIdentity(roomUser.userId),
            'heatValue': proto_utils.buildRoomHeatValue(heartValue),
            'attires': [attire.attrId for attire in roomUser.user.attires],
            'userAttires': [
                proto_utils.encodeUserWoreAttire(wa) for wa in roomUser.user.woreAttires
            ],
            'dukeId': roomUser.user.dukeId,
            'userCount': totalUserCount,
            'userIndex': max(0, totalUserCount - 1),
            'tip': tip
        }

    def _onUserReconnectRoomEvent(self, event):
        msg = self._buildUserEnterRoomMsgOld(event.activeRoom, event.roomUser)
        self._sendMsgToUser(event.roomUser, msg)

    def _onUserEnterRoomEvent(self, event):
        # 房间里广播
        msg = self._buildUserEnterRoomMsgOld(event.activeRoom, event.roomUser)
        self._sendMsgToUser(event.roomUser, msg)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg, [event.roomUser.userId], True, event.roomUser)

    @classmethod
    def _buildUserLeaveRoomMsg(self, activeRoom, roomUser, reason, totalUserCount):
        return {
            'op': 3,
            'msgId': 1002,
            'roomId': activeRoom.roomId,
            'userId': roomUser.userId,
            'userCount': totalUserCount,
            'reason': reason
        }

    @classmethod
    def _buildUserKickoutRoomMsgOld(self, activeRoom, roomUser, reason, reasonInfo, totalUserCount):
        return {
            'op': 3,
            'msgId': 9,
            'roomId': activeRoom.roomId,
            'userId': roomUser.userId if roomUser else 0,
            'userCount': totalUserCount,
            'reason': reason,
            'reasonInfo': reasonInfo
        }

    def _onUserLeaveRoomEvent(self, event):
        if event.reason == UserLeaveRoomReason.BAN_ROOM:
            msg = self._buildUserKickoutRoomMsgOld(event.activeRoom, event.roomUser, event.reason, event.reasonInfo, 0)
            serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId)
            if serverId2UserIds:
                self._sendMsgToUserList(serverId2UserIds, msg, False)
            return

        totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(event.activeRoom.roomId)

        if event.reason == UserLeaveRoomReason.KICKOUT:
            msg = self._buildUserKickoutRoomMsgOld(event.activeRoom, event.roomUser, event.reason, event.reasonInfo, totalUserCount)
            self._sendMsgToUser(event.roomUser, msg)

        msg = self._buildUserLeaveRoomMsg(event.activeRoom, event.roomUser, event.reason, totalUserCount)
        self._sendMsgToUser(event.roomUser, msg)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg, [event.roomUser.userId], True, event.roomUser)

    def _loadRoomMicInfos(self, roomId):
        roomMicStatusMap = RoomServer.roomMicStatusDao.loadRoomMicStatusMap(roomId)
        micCharmMap = fqparty.app.utilService.getRoomMicCharms(roomId)

        # 目前是9麦，可以根据房间类型进行处理
        roomMicInfos = []
        for micId in MicIds.micIDs:
            roomMicStatus = roomMicStatusMap.get(micId)
            if not roomMicStatus:
                roomMicStatus = RoomMicStatus(micId)
            user = None
            heartValue = micCharmMap.get(micId, 0)
            if roomMicStatus.userId != 0:
                user = RoomServer.userCacheDao.loadUser(roomMicStatus.userId)
            roomMicInfos.append(RoomMicInfo(roomMicStatus, user, heartValue))

        return roomMicInfos

    def _loadTeamPKRoom(self, roomId):
        roomTeamPKStatus = RoomServer.roomTeamPKStatusDao.loadRoomTeamPKStatus(roomId)
        if not roomTeamPKStatus or roomTeamPKStatus.isExpire():
            return None

        pkLocationMap = RoomServer.roomPKLocationDao.loadRoomPKLocationMap(roomId, MicIds.pkIDs)
        return RoomTeamPKInfo(roomTeamPKStatus, pkLocationMap, RoomServer.userCacheDao)

    def _loadTeamAcrossRoom(self, roomId):
        roomAcrossPKStatus = RoomServer.roomAcrossPKStatusDao.loadRoomAcrossPKStatus(roomId)
        if not roomAcrossPKStatus or roomAcrossPKStatus.isExpire():
            return None

        return RoomAcrossPKInfo(roomId, roomAcrossPKStatus, RoomServer.userCacheDao)

    def _buildPushRoomInfoMsg(self, activeRoom, roomUser):
        totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(activeRoom.roomId)
        heartValue = fqparty.app.utilService.getRoomHeatScore(activeRoom.roomId)
        roomMicInfos = self._loadRoomMicInfos(activeRoom.roomId)
        roomStatus = RoomServer.roomStatusDao.loadRoomStatus(activeRoom.roomId) or RoomStatus()
        roomTeamPKInfo = self._loadTeamPKRoom(activeRoom.roomId)
        roomAcrossPKInfo = self._loadTeamAcrossRoom(activeRoom.roomId)
        roomPKMode = PKMode.TEAM_PK if roomTeamPKInfo else (PKMode.ACROSS_PK if roomAcrossPKInfo else 0)
        return {
            'op': 2,
            'msgId': 2,
            'audio': proto_utils.getAudioValue(),
            'count': totalUserCount,
            'balance': 0,
            'userIdentity': activeRoom.getUserIdentity(roomUser.userId),
            'isDisableMsg': roomUser.status.disabledMsg and roomUser.user.dukeId < 5,
            'modeName': activeRoom.room.roomType.modeName,
            'roomData': proto_utils.encodeRoomData(activeRoom, roomStatus, roomPKMode),
            'acrossPKData': proto_utils.encodeRoomAcrossPKData(roomAcrossPKInfo) if roomAcrossPKInfo else None,
            'teamPKData': proto_utils.encodeRoomPKData(roomTeamPKInfo) if roomTeamPKInfo else None,
            'microInfos': [proto_utils.encodeRoomMicInfo(roomMicInfo) for roomMicInfo in roomMicInfos],
            'microOrders': None,
            'ranks': None,
            'tips': '',
            'roomOwnerNickName': activeRoom.ownerUser.nickname,
            'roomOwnerHeadUrl': proto_utils.buildImageUrl(activeRoom.ownerUser.avatar),
            'isAttentionRoomOwner': False,
            'hammers': 0,
            'coloredHammers': 0,
            'heatValue': proto_utils.buildRoomHeatValue(heartValue),
            'canBreakEgg': False,
            'heartbeatInterval': 6,
            'heartbeatTimeOutCount': 3,
        }

    def _onPushRoomInfoEvent(self, event):
        msg = self._buildPushRoomInfoMsg(event.activeRoom, event.roomUser)
        self._sendMsgToUser(event.roomUser, msg)

    @classmethod
    def _buildRoomUserUpdateMsg(self, activeRoom, user):
        return {
            'op': 3,
            'msgId': 1013,
            'roomId': activeRoom.roomId,
            'user': proto_utils.encodeUser(user),
        }

    def _onRoomUserUpdateEvent(self, event):
        msg = self._buildRoomUserUpdateMsg(event.activeRoom, event.roomUser.user)
        self._sendMsgToUser(event.roomUser, msg)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg, [event.roomUser.userId], True, event.roomUser)

    def buildLockRoomMsg(self, activeRoom, locked):
        return {
            'op': 3,
            'msgId': 1008,
            'roomId': activeRoom.roomId,
            'isLocked': 1 if locked else 2
        }

    def _onLockRoomEvent(self, event):
        serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId)
        if serverId2UserIds:
            msg = self.buildLockRoomMsg(event.activeRoom, event.locked)
            self._sendMsgToUserList(serverId2UserIds, msg, False)

    @classmethod
    def _buildRoomUserInfoMsg(self, activeRoom, roomUser, isAttention, inTheRoom):
        roomMicStatus = None
        micUserStatus = RoomServer.micUserStatusDao.loadMicUserStatus(activeRoom.roomId, roomUser.userId)
        if micUserStatus and micUserStatus.micId:
            roomMicStatus = RoomServer.roomMicStatusDao.loadRoomMicStatus(activeRoom.roomId, micUserStatus.micId)
        return {
            'op': 2,
            'msgId': 3,
            'roomId': activeRoom.roomId,
            'isAttention': isAttention,
            'micId': micUserStatus.micId if micUserStatus else 0,
            'isDisableMsg':roomUser.status.disabledMsg and roomUser.user.dukeId < 5,
            'isDisabledMicro': roomMicStatus.disabled if roomMicStatus else False,
            'isInTheRoom': inTheRoom,
            'userIdentity': activeRoom.getUserIdentity(roomUser.userId),
            'user': proto_utils.encodeUser(roomUser.user),
            'clientInfo': roomUser.sessionInfo.get('clientInfo', {}),
        }

    def _onPushRoomUserInfoEvent(self, event):
        msg = self._buildRoomUserInfoMsg(event.activeRoom, event.queryRoomUser, event.isAttention, event.inTheRoom)
        self._sendMsgToUser(event.roomUser, msg)

    @classmethod
    def _buildSendMsgToRoomMsg(self, activeRoom, roomUser, msgType, msg):
        return {
            'op': 1,
            'msgId': 1003,
            'roomId': activeRoom.roomId,
            'fromUserId': roomUser.user.userId,
            'fromUserName': roomUser.user.nickname,
            'fromUser': proto_utils.encodeUser(roomUser.user),
            'msgType': msgType,
            'msg': msg
        }

    def _onSendTextMsgToRoomEvent(self, event):
        # 房间里广播
        msg = self._buildSendMsgToRoomMsg(event.activeRoom, event.roomUser, event.msgType, event.msg)
        self._sendMsgToUser(event.roomUser, msg)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg, [event.roomUser.userId], True, event.roomUser)

    @classmethod
    def _buildRoomUserListAllMsg(self, activeRoom, roomUser, pageIndex, pageNum):
        start = pageIndex * pageNum if pageNum else 0
        count = pageNum if pageNum else 20

        userList = []
        isBlockUser, _ = BlackIndustryStrategy.isBlockedUser(roomUser.userId)
        # 首先检查当前用户是不是黑产用户
        if isBlockUser:
            userIds, totalUserCount = _getValidUserIds(roomUser.userId, activeRoom.roomId, start, count)
        else:
            totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(activeRoom.roomId)
            userIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(activeRoom.roomId, start, count)

        for userId in userIds:
            roomUserInfo = RoomServer.roomUserInfoLoader.loadRoomUserInfo(activeRoom.roomId, userId)
            if roomUserInfo:
                userList.append(proto_utils.encodeRoomUserInfo(activeRoom, roomUserInfo))

        return {
            'msgId':22,
            'roomId':activeRoom.roomId,
            'userCount':totalUserCount,
            'pageIndex':pageIndex,
            'totalIndex':int(math.ceil(1.0 * totalUserCount / pageNum)) if pageNum else 1,
            'userList':userList
        }

    def _onPushRoomUserListAllEvent(self, event):
        msg = self._buildRoomUserListAllMsg(event.activeRoom, event.roomUser, event.pageIndex, event.pageNum)
        self._sendMsgToUser(event.roomUser, msg)

    @classmethod
    def _buildRoomUserListMsg(self, activeRoom, roomUser, listType):
        userList = []
        start = 0
        count = 3 if listType == 2 else 20

        isBlockUser, _ = BlackIndustryStrategy.isBlockedUser(roomUser.userId)
        if isBlockUser:
            userIds, totalUserCount = _getValidUserIds(roomUser.userId, activeRoom.roomId, start, count)
        else:
            totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(activeRoom.roomId)
            userIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(activeRoom.roomId, start, count)

        for userId in userIds:
            roomUserInfo = RoomServer.roomUserInfoLoader.loadRoomUserInfo(activeRoom.roomId, userId)
            if roomUserInfo:
                userList.append(proto_utils.encodeRoomUserInfoOld(activeRoom, roomUserInfo))

        return {
            'msgId': 4,
            'type': listType,
            'roomId': activeRoom.roomId,
            'userCount': totalUserCount,
            'userList': userList
        }

    def _onPushRoomUserListEvent(self, event):
        msg = self._buildRoomUserListMsg(event.activeRoom, event.roomUser, event.listType)
        self._sendMsgToUser(event.roomUser, msg)

    @classmethod
    def _buildRoomUserListThreeMsg(self, activeRoom):
        userList = []
        for userId in activeRoom.top3UserIds:
            roomUserInfo = RoomServer.roomUserInfoLoader.loadRoomUserInfo(activeRoom.roomId, userId)
            if roomUserInfo:
                userList.append(proto_utils.encodeRoomUserInfo(activeRoom, roomUserInfo))

        totalUserCount = RoomServer.roomOnlineUserListDao.getRoomOnlineUserCount(activeRoom.roomId)

        return {
            'msgId': 21,
            'roomId': activeRoom.roomId,
            'userCount': totalUserCount,
            'userList': userList
        }

    def _onPushRoomUserListThreeEvent(self, event):
        msg = self._buildRoomUserListThreeMsg(event.activeRoom)
        if event.roomUser:
            self._sendMsgToUser(event.roomUser, msg)
        else:
            serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId)
            if serverId2UserIds:
                self._sendMsgToUserList(serverId2UserIds, msg, False)

    @classmethod
    def _buildPushRoomMsgOld(self, activeRoom, msg, isBroadcast):
        dt = datetime.now()
        return {
            'code': 0,
            'op': 0,
            'msgId': 10003,
            'msgType': 0,
            'micId': 0,
            'emoticonUrl': '',
            'createTime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'roomId': activeRoom.roomId if not isBroadcast else 0,
            'fromUser': None,
            'fromUserId': 0,
            'fromUserName': '',
            'msg': msg,
            'type': 0
        }

    def _onPushRoomMsgEvent(self, event):
        serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId, event.excludeUserIds)
        if serverId2UserIds:
            msg = self._buildPushRoomMsgOld(event.activeRoom, event.msg, event.isBroadcast)
            if not event.canIgnore or not event.canntIgnoreUserIds:
                self._sendMsgToUserList(serverId2UserIds, msg, event.canIgnore)
            else:
                for serverId, userIds in serverId2UserIds.iteritems():
                    cannotIgnoreUserIds = []
                    canIgnoreUserIds = []
                    for userId in userIds:
                        if userId in event.canntIgnoreUserIds:
                            cannotIgnoreUserIds.append(userId)
                        else:
                            canIgnoreUserIds.append(userId)
                    if cannotIgnoreUserIds:
                        self._sendMsgToServerUserList(serverId, cannotIgnoreUserIds, msg, False)
                    if canIgnoreUserIds:
                        self._sendMsgToServerUserList(serverId, canIgnoreUserIds, msg, True)

    def _onPushRoomLedMsgEvent(self, event):
        serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId, event.excludeUserIds)
        if serverId2UserIds:
            msg = {
                'msgId': 10004,
                'roomId': event.activeRoom.roomId,
                'msg': event.msg,
            }
            self._sendMsgToUserList(serverId2UserIds, msg, False)

    def _onSendRoomMsgEvent(self, event):
        serverId2UserIds = self._dispatchRoomUsers(event.activeRoom.roomId, event.excludeUserIds)
        if serverId2UserIds:
            if event.excludeUserIds:
                # 剔除的第一个用户就是登录用户
                userId = event.excludeUserIds[0]
                if BlackIndustryStrategy.isProtectedUser(userId):
                    newServerId2UserIds = {}
                    for serverId, userIds in serverId2UserIds.items():
                        blockInfo = BlackIndustryStrategy(userId, userIds, FILTER_HEICHAN_USER)
                        newServerId2UserIds[serverId] = blockInfo.afterFilter()
                    serverId2UserIds = newServerId2UserIds

            self._sendMsgToUserList(serverId2UserIds, event.msg, event.canIgnore)

    def _onSendRoomMsgToUserEvent(self, event):
        self._sendMsgToUser(event.roomUser, event.msg)

    @classmethod
    def _buildDisableUserMsgMsgOld(self, activeRoom, roomUser):
        return {
            'op': 3,
            'msgId': 8,
            'roomId': activeRoom.roomId,
            'userId': roomUser.userId,
            'isDisableMsg':roomUser.status.disabledMsg and roomUser.user.dukeId < 5
        }

    def _onDisabledUserMsgEvent(self, event):
        msg = self._buildDisableUserMsgMsgOld(event.activeRoom, event.roomUser)
        self._sendMsgToUser(event.roomUser, msg)

    def _sendMsgToAllRoomServer(self, roomId, msg, excludeUserIds=None, canIgnore=False, roomUser=None):
        # 发消息给本server的用户
        serverId2UserIds = self._dispatchRoomUsers(roomId, excludeUserIds)
        if serverId2UserIds:
            if roomUser and BlackIndustryStrategy.isProtectedUser(roomUser.userId):
                # 过滤掉黑产用户
                newServerId2UserIds = {}
                for serverId, userIds in serverId2UserIds.items():
                    blockInfo = BlackIndustryStrategy(roomUser.userId, userIds, FILTER_HEICHAN_USER)
                    newServerId2UserIds[serverId] = blockInfo.afterFilter()
                serverId2UserIds = newServerId2UserIds

            self._sendMsgToUserList(serverId2UserIds, msg, canIgnore)

        room_remote_proxy.sendRoomMsgToAllRoomServer(roomId, msg, excludeUserIds, [tomato.app.serverId], canIgnore)

    def _sendMsgToUser(self, roomUser, msg):
        frontendId = roomUser.frontendId
        if frontendId:
            if isstring(msg):
                msgdata = msg
            else:
                assert (isinstance(msg, dict))
                msgdata = strutil.jsonDumps(msg)
            if ttlog.isDebugEnabled():
                ttlog.debug('RoomProto._sendMsgToUser',
                            'frontendId=', frontendId,
                            'userId=', roomUser.userId,
                            'msg=', msgdata)
            session_remote_proxy.pushRawData(msgdata, roomUser.frontendId, roomUser.userId)

    def _sendMsgToServerUserList(self, serverId, userIds, msg, canIgnore):
        if isstring(msg):
            msgdata = msg
        else:
            assert (isinstance(msg, dict))
            msgdata = strutil.jsonDumps(msg)
        if ttlog.isDebugEnabled():
            ttlog.debug('RoomProto._sendMsgToServerUserList',
                        'frontendId=', serverId,
                        'userIds=', userIds,
                        'canIgnore=', canIgnore,
                        'msg=', msgdata)
        session_remote_proxy.pushRawData(msgdata, serverId, userIds, canIgnore)

    def _sendMsgToUserList(self, serverId2UserIds, msg, canIgnore):
        if isstring(msg):
            msgdata = msg
        else:
            assert (isinstance(msg, dict))
            msgdata = strutil.jsonDumps(msg)
        for serverId, userIds in serverId2UserIds.iteritems():
            if ttlog.isDebugEnabled():
                ttlog.debug('RoomProto._sendMsgToUserList',
                            'frontendId=', serverId,
                            'userIds=', userIds,
                            'canIgnore=', canIgnore,
                            'msg=', msgdata)
            session_remote_proxy.pushRawData(msgdata, serverId, userIds, canIgnore)

    def _dispatchRoomUsers(self, roomId, excludeUserIds=None):
        # map<serverId, list<userId>>
        ret = {}
        roomUserSet = RoomServer.roomUserManager.getRoomUsersByRoomId(roomId)
        if roomUserSet:
            for roomUser in roomUserSet:
                if excludeUserIds and roomUser.userId in excludeUserIds:
                    continue
                frontendId = roomUser.frontendId
                if frontendId:
                    userIdList = ret.get(frontendId)
                    if not userIdList:
                        userIdList = []
                        ret[frontendId] = userIdList
                    userIdList.append(roomUser.userId)
        return ret

