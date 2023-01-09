# -*- coding:utf-8 -*-
'''
Created on 2020年11月6日

@author: zhaojiangang
'''
from datetime import datetime
from sre_compile import isstring
import time

import fqparty
from fqparty.servers.mic import MicServer
from fqparty.domain.events.events import UserOnMicEvent, UserLeaveMicEvent, MicLockEvent, MicDisableEvent, MicCountdownEvent, \
    UserInviteMicEvent, RoomPKStartEvent, RoomPKEndEvent, RoomPKAddCountdownEvent, RoomUpdatePKRankEvent, RoomCreateAcrossPKEvent, \
    RoomSponsoreAcrossPKEvent, RoomAcrossPKListEvent, RoomReplyAcrossPKEvent, RoomCreateAcrossPKListEvent, RoomAcrossPKStartEvent, \
    RoomAcrossPKEndEvent, RoomAcrossPKingDataEvent, RoomPKSearchEvent, UserOnPKLocationEvent, UserLeavePKLocationEvent, \
    UserInvitePKLocationEvent, DisablePKLocationEvent, LockPKLocationEvent, PKLocationCountdownEvent, RoomUserUpdateEvent, \
    RoomDisabledMsgEvent, MicEmoticonStartEvent, MicEmoticonFinishEvent
from fqparty.domain.models.room import PKTeam
from fqparty.domain.room.room import RoomMicInfo, RoomTeamPKInfo, RoomAcrossPKInfo
from fqparty.proxy.room import room_remote_proxy
from fqparty.utils import proto_utils
from tomato.common.proxy import session_remote_proxy
from tomato.utils import strutil, ttlog


class MicProto(object):
    def setupEvents(self):
        fqparty.app.on(UserOnMicEvent, self._onUserOnMicEvent)
        fqparty.app.on(UserLeaveMicEvent, self._onUserLeaveMicEvent)
        fqparty.app.on(UserInviteMicEvent, self._onUserInviteMicEvent)
        fqparty.app.on(MicDisableEvent, self._onMicDisableEvent)
        fqparty.app.on(MicLockEvent, self._onMicLockEvent)
        fqparty.app.on(MicCountdownEvent, self._onMicCountdownEvent)
        fqparty.app.on(MicEmoticonStartEvent, self._onMicEmoticonStartEvent)
        fqparty.app.on(MicEmoticonFinishEvent, self._onMicEmoticonFinishEvent)
        fqparty.app.on(RoomPKStartEvent, self._onRoomPKStartEvent)
        fqparty.app.on(RoomPKEndEvent, self._onRoomPKEndEvent)
        fqparty.app.on(UserOnPKLocationEvent, self._onUserOnPKLocationEvent)
        fqparty.app.on(UserLeavePKLocationEvent, self._onUserLeavePKLocationEvent)
        fqparty.app.on(UserInvitePKLocationEvent, self._onUserInvitePKLocationEvent)
        fqparty.app.on(DisablePKLocationEvent, self._onDisablePKLocationEvent)
        fqparty.app.on(LockPKLocationEvent, self._onLockPKLocationEvent)
        fqparty.app.on(PKLocationCountdownEvent, self._onPKLocationCountdownEvent)
        fqparty.app.on(RoomPKAddCountdownEvent, self._onRoomPKAddCountdownEvent)
        fqparty.app.on(RoomUpdatePKRankEvent, self._onRoomUpdatePKRankEvent)
        fqparty.app.on(RoomCreateAcrossPKEvent, self._onRoomCreateAcrossPKEvent)
        fqparty.app.on(RoomCreateAcrossPKListEvent, self._onRoomCreateAcrossPKListEvent)
        fqparty.app.on(RoomSponsoreAcrossPKEvent, self._onRoomSponsoreAcrossPKEvent)
        fqparty.app.on(RoomReplyAcrossPKEvent, self._onRoomReplyAcrossPKEvent)
        fqparty.app.on(RoomAcrossPKListEvent, self._onRoomAcrossPKListEvent)
        fqparty.app.on(RoomAcrossPKStartEvent, self._onRoomAcrossPKStartEvent)
        fqparty.app.on(RoomAcrossPKEndEvent, self._onRoomAcrossPKEndEvent)
        fqparty.app.on(RoomAcrossPKingDataEvent, self._onRoomAcrossPKingDataEvent)
        fqparty.app.on(RoomPKSearchEvent, self._onRoomPKSearchEvent)
        fqparty.app.on(RoomDisabledMsgEvent, self._onRoomDisabledMsgEvent)

    def _sendMsgToUser(self, userId, frontendId, msg):
        if isstring(msg):
            msgdata = msg
        else:
            assert (isinstance(msg, dict))
            msgdata = strutil.jsonDumps(msg)
        if ttlog.isDebugEnabled():
            ttlog.debug('_sendMsgToUser',
                        'userId=', userId,
                        'msg=', msgdata)
        session_remote_proxy.pushRawData(msgdata, frontendId, userId)

    @classmethod
    def _buildUserOnMicMsg(self, activeRoom, micUser, mic):
        heartValue = fqparty.app.utilService.getRoomMicCharm(activeRoom.roomId, mic.micId)
        roomMicInfo = RoomMicInfo(mic.status, micUser.user, heartValue)
        return {
            'op': 3,
            'msgId': 1006,
            'roomId': activeRoom.roomId,
            'userId': micUser.userId,
            'micId': mic.micId,
            'userIdentity': activeRoom.getUserIdentity(micUser.userId),
            'microInfo': proto_utils.encodeRoomMicInfo(roomMicInfo),
        }

    def _onUserOnMicEvent(self, event):

        # 推送mic房间的消息给userRoom房间
        msg = self._buildUserOnMicMsg(event.activeRoom, event.micUser, event.mic)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildUserLeaveMicMsg(self, activeRoom, userId, mic):
        return {
            'op': 3,
            'msgId': 1007,
            'roomId': activeRoom.roomId,
            'userId': userId,
            'micId': mic.micId
        }

    def _onUserLeaveMicEvent(self, event):
        # 推送mic房间的消息给userRoom房间
        msg = self._buildUserLeaveMicMsg(event.activeRoom, event.userId, event.mic)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildInviteMicMsg(self, activeRoom, userId, mic):
        return {
            'msgId': 7,
            'roomId': activeRoom.roomId,
            'micId': mic.micId,
            'userId': userId
        }

    def _onUserInviteMicEvent(self, event):
        # 推送mic房间的消息给userRoom房间
        msg = self._buildInviteMicMsg(event.activeRoom, event.userId, event.mic)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.inviteeUserId, msg)

    @classmethod
    def _buildDisableMicMsg(self, activeRoom, mic):
        return {
            'op': 3,
            'msgId': 1010,
            'roomId': activeRoom.roomId,
            'micId': mic.micId,
            'isLocked': 1 if mic.status.disabled else 0
        }

    def _onMicDisableEvent(self, event):
        msg = self._buildDisableMicMsg(event.activeRoom, event.mic)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildLockMicMsg(self, activeRoom, mic):
        return {
            'op': 3,
            'msgId': 1009,
            'roomId': activeRoom.roomId,
            'micId': mic.micId,
            'isLocked': 1 if mic.status.locked else 0
        }

    def _onMicLockEvent(self, event):
        # 推送mic房间的消息给userRoom房间
        msg = self._buildLockMicMsg(event.activeRoom, event.mic)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildCountdownMicMsg(self, mic):
        countdownTime = mic.status.countdownTime
        return {
            'op': 3,
            'msgId': 1005,
            'roomId': mic.activeRoom.roomId,
            'micId': mic.micId,
            'countdownTime':datetime.fromtimestamp(countdownTime).strftime('%Y-%m-%dT%H:%M:%S.0+08:00') if countdownTime != 0 else '',
            'duration':mic.status.countdownDuration,
        }

    def _onMicCountdownEvent(self, event):
        # 推送mic房间的消息给userRoom房间
        msg = self._buildCountdownMicMsg(event.mic)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildMicEmoticonStartMsg(self, activeRoom, user, mic, emoticon):
        return {
            'op': 1,
            'msgId': 1003,
            'roomId': activeRoom.roomId,
            'fromUserId': user.userId,
            'fromUserName': user.nickname,
            'fromUser': proto_utils.encodeUser(user),
            'micId': mic.micId,
            'msgType': 2,
            'msg': strutil.jsonDumps(emoticon.emoticonId),
            'emoticonUrl': proto_utils.buildImageUrl(emoticon.animation)
        }

    def _onMicEmoticonStartEvent(self, event):
        msg = self._buildMicEmoticonStartMsg(event.activeRoom, event.user, event.mic, event.emoticon)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildMicEmoticonFinishMsg(self, activeRoom, user, mic, emoticon, emoticonUrl):
        return {
            'op': 1,
            'msgId': 1003,
            'roomId': activeRoom.roomId,
            'fromUserId': user.userId,
            'fromUserName': user.nickname,
            'fromUser': proto_utils.encodeUser(user),
            'micId': mic.micId,
            'msgType': 3,
            'msg': strutil.jsonDumps(emoticon.emoticonId),
            'emoticonUrl': proto_utils.buildImageUrl(emoticonUrl)
        }

    def _onMicEmoticonFinishEvent(self, event):
        msg = self._buildMicEmoticonFinishMsg(event.activeRoom, event.user, event.mic, event.emoticon, event.emoticonFinishImage)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildRoomPKStartMsg(self, activeRoom):
        roomTeamPKInfo = RoomTeamPKInfo(activeRoom.roomTeamPK.status, activeRoom.roomTeamPK.pkLocationMap, MicServer.userCacheDao)
        return {
            'op': 2,
            'msgId': 2001,
            'roomId': activeRoom.roomId,
            'pkData': proto_utils.encodeRoomPKData(roomTeamPKInfo)
        }

    def _onRoomPKStartEvent(self, event):
        msg = self._buildRoomPKStartMsg(event.activeRoom)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildRoomPKEndMsg(self, activeRoom, roomTeamPK, winPK):
        roomTeamPKInfo = RoomTeamPKInfo(roomTeamPK.status, roomTeamPK.pkLocationMap, MicServer.userCacheDao)
        return {
            'op': 2,
            'msgId': 2002,
            'roomId': activeRoom.roomId,
            'winPK': winPK,
            'redTotalPKValue': sum(roomTeamPKInfo.status.redPKMap.values()),
            'blueTotalPKValue': sum(roomTeamPKInfo.status.bluePKMap.values()),
            'redList': [proto_utils.encodeRoomPkUser(pkuser, pkuser.totalPkValue) for pkuser in roomTeamPKInfo.getCharmUsers(PKTeam.RED_TEAM)],
            'blueList': [proto_utils.encodeRoomPkUser(pkuser, pkuser.totalPkValue) for pkuser in roomTeamPKInfo.getCharmUsers(PKTeam.BLUE_TEAM)],
            'contributionList': [proto_utils.encodeRoomPkUser(pkuser, pkuser.totalContributeValue) for pkuser in roomTeamPKInfo.getMVPUsers(winPK)],
        }

    def _onRoomPKEndEvent(self, event):
        msg = self._buildRoomPKEndMsg(event.activeRoom, event.roomTeamPK, event.winPK)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildUserOnPKLocationMsg(self, activeRoom, userId, pkLocation):
        return {
                'msgId': 2004,
                'roomId': activeRoom.roomId,
                'userId': userId,
                'micId': pkLocation.micId,
                'location': pkLocation.location
            }

    def _onUserOnPKLocationEvent(self, event):
        msg = self._buildUserOnPKLocationMsg(event.activeRoom, event.userId, event.pkLocation)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildUserLeavePKLocationMsg(self, activeRoom, userId, pkLocation):
        return {
                'msgId': 2005,
                'roomId': activeRoom.roomId,
                'userId': userId,
                'micId': pkLocation.micId,
                'location': pkLocation.location,
            }

    def _onUserLeavePKLocationEvent(self, event):
        msg = self._buildUserLeavePKLocationMsg(event.activeRoom, event.userId, event.pkLocation)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildUserInvitePKLocationMsg(self, activeRoom, inviteUserId, pkLocation):
        return {
                'msgId': 2006,
                'roomId': activeRoom.roomId,
                'location': pkLocation.location,
                'userId': inviteUserId
            }

    def _onUserInvitePKLocationEvent(self, event):
        msg = self._buildUserInvitePKLocationMsg(event.activeRoom, event.userId, event.pkLocation)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.inviteeUserId, msg)

    @classmethod
    def _buildDisablePKLocationMsg(self, activeRoom, pkLocation):
        return {
                'msgId': 2008,
                'roomId': activeRoom.roomId,
                'location': pkLocation.location,
                'isDisabled': 1 if pkLocation.disabled else 0
            }

    def _onDisablePKLocationEvent(self, event):
        msg = self._buildDisablePKLocationMsg(event.activeRoom, event.pkLocation)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildLockPKLocationMsg(self, activeRoom, pkLocation):
        return {
                'msgId': 2007,
                'roomId': activeRoom.roomId,
                'location': pkLocation.location,
                'isLocked': 1 if pkLocation.locked else 0
            }

    def _onLockPKLocationEvent(self, event):
        msg = self._buildLockPKLocationMsg(event.activeRoom, event.pkLocation)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildPKLocationCountdownMsg(self, activeRoom, pkLocation):
        return {
                'msgId': 2010,
                'roomId': activeRoom.roomId,
                'location': pkLocation.location,
                'startTime': pkLocation.countdownTime,
                'duration':max(0, pkLocation.countdownTime + pkLocation.countdownDuration - int(time.time()))
            }

    def _onPKLocationCountdownEvent(self, event):
        msg = self._buildPKLocationCountdownMsg(event.activeRoom, event.pkLocation)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildRoomPKAddCountdownMsg(self, activeRoom, duration):
        return {
            'op': 2,
            'msgId': 2003,
            'roomId': activeRoom.roomId,
            'startTime':activeRoom.roomTeamPK.status.startTime,
            'countdown':activeRoom.roomTeamPK.status.countdown,
            'duration': duration,
        }

    def _onRoomPKAddCountdownEvent(self, event):
        msg = self._buildRoomPKAddCountdownMsg(event.activeRoom, event.duration)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildUpdatePKRankMsg(self, activeRoom):
        roomTeamPKInfo = RoomTeamPKInfo(activeRoom.roomTeamPK.status, activeRoom.roomTeamPK.pkLocationMap, MicServer.userCacheDao)
        charmUser = roomTeamPKInfo.getFirstCharmUser()
        mvpUser = roomTeamPKInfo.getMVPUser()
        redTotalPKValue = sum(roomTeamPKInfo.status.redPKMap.values())
        blueTotalPKValue = sum(roomTeamPKInfo.status.bluePKMap.values())
        return {
            'op': 2,
            'msgId': 2009,
            'roomId': activeRoom.roomId,
            'redTotalPKValue': redTotalPKValue,
            'blueTotalPKValue': blueTotalPKValue,
            'pkLocationCharmList': proto_utils.encodePKLocationCharmList(roomTeamPKInfo),
            'charmUser': proto_utils.encodeRoomPkUser(charmUser, charmUser.totalPkValue) if charmUser else None,
            'mvpUser': proto_utils.encodeRoomPkUser(mvpUser, mvpUser.totalContributeValue) if mvpUser else None,
        }

    def _onRoomUpdatePKRankEvent(self, event):
        msg = self._buildUpdatePKRankMsg(event.activeRoom)
        if event.userId:
            room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)
        else:
            self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildCreateAcrossPKMsg(self, activeRoom, acrossPK, cancel):
        return {
                'op': 2,
                'msgId': 3001,
                'roomId': activeRoom.roomId,
                'cancel': cancel,
                'pkData':acrossPK.toViewJson() if acrossPK else None
            }

    def _onRoomCreateAcrossPKEvent(self, event):
        msg = self._buildCreateAcrossPKMsg(event.activeRoom, event.acrossPK, event.cancel)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildCreateAcrossPKListMsg(self, activeRoom, acrossPKList):
        return {
                'op': 2,
                'msgId': 3002,
                'roomId': activeRoom.roomId,
                'acrossPKList':[acrossPK.toViewJson() for acrossPK in acrossPKList]
            }

    def _onRoomCreateAcrossPKListEvent(self, event):
        msg = self._buildCreateAcrossPKListMsg(event.activeRoom, event.acrossPKList)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildSponsoreAcrossPKMsg(self, activeRoom, acrossPK):
        return {
                'op': 2,
                'msgId': 3003,
                'roomId': activeRoom.roomId,
                'pkData': acrossPK.toViewJson()
            }

    def _onRoomSponsoreAcrossPKEvent(self, event):
        msg = self._buildSponsoreAcrossPKMsg(event.activeRoom, event.acrossPK)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildReplyAcrossPKMsg(self, activeRoom, pkRoomId, accept):
        return {
                'op': 2,
                'msgId': 3004,
                'roomId': activeRoom.roomId,
                'pkRoomId': pkRoomId,
                'accept': accept
            }

    def _onRoomReplyAcrossPKEvent(self, event):
        msg = self._buildReplyAcrossPKMsg(event.activeRoom, event.targetRoomId, event.accept)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildAcrossPKListMsg(self, activeRoom, acrossPKList):
        return {
            'op': 2,
            'msgId': 3005,
            'roomId': activeRoom.roomId,
            'acrossPKList': [acrossPK.toViewJson() for acrossPK in acrossPKList]
        }

    def _onRoomAcrossPKListEvent(self, event):
        msg = self._buildAcrossPKListMsg(event.activeRoom, event.acrossPKList)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildAcrossPKStartMsg(self, activeRoom):
        roomAcrossPKInfo = RoomAcrossPKInfo(activeRoom.roomId, activeRoom.acrossRoomPK.status, MicServer.userCacheDao)
        return {
                'op': 2,
                'msgId': 3006,
                'roomId': activeRoom.roomId,
                'pkData': proto_utils.encodeRoomAcrossPKData(roomAcrossPKInfo),
            }

    def _onRoomAcrossPKStartEvent(self, event):
        msg = self._buildAcrossPKStartMsg(event.activeRoom)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildAcrossPKEndMsg(self, activeRoom, acrossRoomPK, winPK, winRoomId):
        roomAcrossPKInfo = RoomAcrossPKInfo(activeRoom.roomId, acrossRoomPK.status, MicServer.userCacheDao)
        return {
                'op': 2,
                'msgId': 3007,
                'roomId': activeRoom.roomId,
                'winPK': winPK,
                'winRoomId': winRoomId,
                'redData':{
                    'pkValue': roomAcrossPKInfo.getTotalPKValue(PKTeam.RED_TEAM),
                    'roomName': roomAcrossPKInfo.acrossPK.roomName,
                    'name': roomAcrossPKInfo.acrossPK.userName,
                    'avater': proto_utils.buildImageUrl(roomAcrossPKInfo.acrossPK.userAvater),
                },
                'blueData': {
                    'pkValue': roomAcrossPKInfo.getTotalPKValue(PKTeam.BLUE_TEAM),
                    'name': roomAcrossPKInfo.status.pkUserName,
                    'roomName': roomAcrossPKInfo.status.pkRoomName,
                    'avater': proto_utils.buildImageUrl(roomAcrossPKInfo.status.pkUserAvater),
                }
            }

    def _onRoomAcrossPKEndEvent(self, event):
        msg = self._buildAcrossPKEndMsg(event.activeRoom, event.acrossRoomPK, event.winPK, event.winRoomId)
        self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildAcrossPKingDataMsg(self, activeRoom):
        roomAcrossPKInfo = RoomAcrossPKInfo(activeRoom.roomId, activeRoom.acrossRoomPK.status, MicServer.userCacheDao)
        return {
                'op': 2,
                'msgId': 3008,
                'roomId': activeRoom.roomId,
                'pkData': proto_utils.encodeRoomAcrossPKData(roomAcrossPKInfo),
            }

    def _onRoomAcrossPKingDataEvent(self, event):
        msg = self._buildAcrossPKingDataMsg(event.activeRoom)
        if event.userId:
            room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)
        else:
            self._sendMsgToAllRoomServer(event.activeRoom.roomId, msg)

    @classmethod
    def _buildPKSearchMsg(self, activeRoom, searchRoom, searchRoomOwnerUser, acrossPK, status):
        return {
                'op': 2,
                'msgId': 3009,
                'roomId': activeRoom.roomId,
                'searchRoomId':searchRoom.roomId,
                'searchPrettyRoomId': searchRoom.prettyRoomId,
                'roomName': searchRoom.roomName,
                'ownerName': searchRoomOwnerUser.nickname,
                'ownerAvater': proto_utils.buildImageUrl(searchRoomOwnerUser.avatar),
                'punishment': acrossPK.punishment if acrossPK else "",
                'countdown': acrossPK.countdown if acrossPK else 0,
                'duration': acrossPK.duration if acrossPK else 0,
                'status': status
            }

    def _onRoomPKSearchEvent(self, event):
        msg = self._buildPKSearchMsg(event.activeRoom, event.searchRoom, event.searchRoomOwnerUser, event.acrossPK, event.status)
        room_remote_proxy.sendRoomMsgToUser(event.activeRoom.roomId, event.userId, msg)

    @classmethod
    def _buildRoomDisableMsgMsg(self, roomId, roomStatus):
        return {
            'op': 3,
            'msgId': 1011,
            'roomId': roomId,
            'isDisabled': roomStatus.disabledMsg
        }

    def _onRoomDisabledMsgEvent(self, event):
        msg = self._buildRoomDisableMsgMsg(event.roomId, event.roomStatus)
        self._sendMsgToAllRoomServer(event.roomId, msg)

    def _sendMsgToAllRoomServer(self, roomId, msg, excludeUserIds=None):
        room_remote_proxy.sendRoomMsgToAllRoomServer(roomId, msg, excludeUserIds, [])
