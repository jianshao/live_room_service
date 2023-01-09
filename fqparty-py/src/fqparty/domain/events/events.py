# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''
from tomato.utils.obser import TTObserEvent


class UserLoginEvent(TTObserEvent):
    def __init__(self, userId, user):
        super(UserLoginEvent, self).__init__()
        # 哪个用户
        self.userId = userId
        # 用户信息
        self.user = user


class UserLogoutEvent(TTObserEvent):
    def __init__(self, userId):
        super(UserLogoutEvent, self).__init__()
        # 用户ID
        self.userId = userId


class UserHeartbeatEvent(TTObserEvent):
    def __init__(self, roomUser, duration):
        super(UserHeartbeatEvent, self).__init__()
        self.roomUser = roomUser
        self.duration = duration


class ActiveRoomEvent(TTObserEvent):
    def __init__(self, activeRoom):
        super(ActiveRoomEvent, self).__init__()
        # 哪个房间
        self.activeRoom = activeRoom


class ActiveRoomUserEvent(ActiveRoomEvent):
    def __init__(self, activeRoom, roomUser):
        super(ActiveRoomUserEvent, self).__init__(activeRoom)
        self.roomUser = roomUser


class RoomDisabledMsgEvent(TTObserEvent):
    def __init__(self, roomId, roomStatus):
        super(RoomDisabledMsgEvent, self).__init__()
        self.roomId = roomId
        self.roomStatus = roomStatus


class MicActiveRoomEvent(TTObserEvent):
    def __init__(self, activeRoom):
        super(MicActiveRoomEvent, self).__init__()
        # 哪个房间
        self.activeRoom = activeRoom


class MicActiveRoomUserEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, userId):
        super(MicActiveRoomUserEvent, self).__init__(activeRoom)
        self.userId = userId


'''麦位房间事件'''
class MicRoomLoadEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(MicRoomLoadEvent, self).__init__(activeRoom)


class MicRoomRemoveEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(MicRoomRemoveEvent, self).__init__(activeRoom)


class RoomPKStartEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(RoomPKStartEvent, self).__init__(activeRoom)


class RoomPKEndEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, roomTeamPK, winPK):
        super(RoomPKEndEvent, self).__init__(activeRoom)
        self.roomTeamPK = roomTeamPK
        self.winPK = winPK


class RoomPKExpireEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(RoomPKExpireEvent, self).__init__(activeRoom)


class RoomPKAddCountdownEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, duration):
        super(RoomPKAddCountdownEvent, self).__init__(activeRoom)
        self.duration = duration


class RoomAcrossPKStartEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(RoomAcrossPKStartEvent, self).__init__(activeRoom)


class RoomAcrossPKEndEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, acrossRoomPK, winPK, winRoomId):
        super(RoomAcrossPKEndEvent, self).__init__(activeRoom)
        self.acrossRoomPK = acrossRoomPK
        self.winPK = winPK
        self.winRoomId = winRoomId


class RoomAcrossPKExpireEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom):
        super(RoomAcrossPKExpireEvent, self).__init__(activeRoom)


class MicLockEvent(MicActiveRoomEvent):
    '''
    锁麦
    '''
    def __init__(self, activeRoom, mic):
        super(MicLockEvent, self).__init__(activeRoom)
        # 哪个麦
        self.mic = mic


class MicDisableEvent(MicActiveRoomEvent):
    '''
    禁麦
    '''
    def __init__(self, activeRoom, mic):
        super(MicDisableEvent, self).__init__(activeRoom)
        # 哪个麦
        self.mic = mic


class DisablePKLocationEvent(MicActiveRoomEvent):
    '''
    禁麦
    '''
    def __init__(self, activeRoom, pkLocation):
        super(DisablePKLocationEvent, self).__init__(activeRoom)
        # pkLocation
        self.pkLocation = pkLocation


class LockPKLocationEvent(MicActiveRoomEvent):
    '''
    锁麦
    '''
    def __init__(self, activeRoom, pkLocation):
        super(LockPKLocationEvent, self).__init__(activeRoom)
        self.pkLocation = pkLocation


class PKLocationCountdownEvent(MicActiveRoomEvent):
    '''
    倒计时
    '''
    def __init__(self, activeRoom, pkLocation):
        super(PKLocationCountdownEvent, self).__init__(activeRoom)
        # 哪个麦
        self.pkLocation = pkLocation


class MicCountdownEvent(MicActiveRoomEvent):
    '''
    倒计时
    '''
    def __init__(self, activeRoom, mic):
        super(MicCountdownEvent, self).__init__(activeRoom)
        # 哪个麦
        self.mic = mic


class MicEmoticonStartEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, mic, user, emoticon, finishImage, finishTime):
        super(MicEmoticonStartEvent, self).__init__(activeRoom)
        self.mic = mic
        self.user = user
        self.emoticon = emoticon
        self.finishImage = finishImage
        self.finishTime = finishTime


class MicEmoticonFinishEvent(MicActiveRoomEvent):
    def __init__(self, activeRoom, mic, user, emoticon, emoticonFinishImage):
        super(MicEmoticonFinishEvent, self).__init__(activeRoom)
        self.mic = mic
        self.user = user
        self.emoticon = emoticon
        self.emoticonFinishImage = emoticonFinishImage
        

class RoomUpdatePKRankEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId=None):
        super(RoomUpdatePKRankEvent, self).__init__(activeRoom, userId)


class RoomCreateAcrossPKListEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, acrossPKList):
        super(RoomCreateAcrossPKListEvent, self).__init__(activeRoom, userId)
        self.acrossPKList = acrossPKList


class RoomCreateAcrossPKEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, acrossPK, cancel=0):
        super(RoomCreateAcrossPKEvent, self).__init__(activeRoom, userId)
        self.acrossPK = acrossPK
        self.cancel = cancel


class RoomSponsoreAcrossPKEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, acrossPK):
        super(RoomSponsoreAcrossPKEvent, self).__init__(activeRoom, userId)
        self.acrossPK = acrossPK


class RoomReplyAcrossPKEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, targetRoomId, accept):
        super(RoomReplyAcrossPKEvent, self).__init__(activeRoom, userId)
        self.targetRoomId = targetRoomId
        self.accept = accept


class RoomAcrossPKListEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, acrossPKList):
        super(RoomAcrossPKListEvent, self).__init__(activeRoom, userId)
        self.acrossPKList = acrossPKList


class RoomAcrossPKingDataEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId):
        super(RoomAcrossPKingDataEvent, self).__init__(activeRoom, userId)


class RoomPKSearchEvent(MicActiveRoomUserEvent):
    def __init__(self, activeRoom, userId, searchRoom, searchRoomOwnerUser, acrossPK, status):
        super(RoomPKSearchEvent, self).__init__(activeRoom, userId)
        self.searchRoom = searchRoom
        self.searchRoomOwnerUser = searchRoomOwnerUser
        self.acrossPK = acrossPK
        self.status = status


class UserOnMicEvent(MicActiveRoomUserEvent):
    '''
    用户上麦
    '''
    def __init__(self, activeRoom, micUser, mic):
        super(UserOnMicEvent, self).__init__(activeRoom, micUser.userId)
        # 上了哪个麦
        self.mic = mic
        self.micUser = micUser


class UserLeaveMicEvent(MicActiveRoomUserEvent):
    '''
    用户下麦
    '''
    def __init__(self, activeRoom, micUserStatus, mic, reason):
        super(UserLeaveMicEvent, self).__init__(activeRoom, micUserStatus.userId)
        # 下了哪个麦
        self.mic = mic
        self.micUserStatus = micUserStatus
        self.reason = reason  #下麦的原因


class UserInviteMicEvent(MicActiveRoomUserEvent):
    '''
    用户邀请麦
    '''
    def __init__(self, activeRoom, userId, inviteeUserId, mic):
        super(UserInviteMicEvent, self).__init__(activeRoom, userId)
        # 受邀的玩家
        self.inviteeUserId = inviteeUserId
        # 哪个麦
        self.mic = mic


class UserOnPKLocationEvent(MicActiveRoomUserEvent):
    '''
    用户上麦
    '''
    def __init__(self, activeRoom, userId, pkLocation):
        super(UserOnPKLocationEvent, self).__init__(activeRoom, userId)
        self.pkLocation = pkLocation


class UserLeavePKLocationEvent(MicActiveRoomUserEvent):
    '''
    用户下麦
    '''
    def __init__(self, activeRoom, userId, pkLocation, reason):
        super(UserLeavePKLocationEvent, self).__init__(activeRoom, userId)
        self.reason = reason  #下麦的原因
        self.pkLocation = pkLocation


class UserInvitePKLocationEvent(MicActiveRoomUserEvent):
    '''
    用户邀请麦
    '''
    def __init__(self, activeRoom, inviteUserId, inviteeUserId, pkLocation):
        super(UserInvitePKLocationEvent, self).__init__(activeRoom, inviteUserId)
        # 受邀的玩家
        self.inviteeUserId = inviteeUserId
        # pkMic
        self.pkLocation = pkLocation


'''用户房间事件'''

class DisabledUserMsgEvent(ActiveRoomUserEvent):
    '''
    用户禁言
    '''
    def __init__(self, activeRoom, roomUser, disabled):
        super(DisabledUserMsgEvent, self).__init__(activeRoom, roomUser)
        self.disabled = disabled


class RoomUserUpdateEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser):
        super(RoomUserUpdateEvent, self).__init__(activeRoom, roomUser)


class PushRoomMsgEvent(ActiveRoomEvent):
    def __init__(self, activeRoom, msg, isBroadcast, excludeUserIds=[], canIgnore=False, canntIgnoreUserIds=set()):
        super(PushRoomMsgEvent, self).__init__(activeRoom)
        self.msg = msg
        self.isBroadcast = isBroadcast
        self.excludeUserIds = excludeUserIds
        self.canIgnore = canIgnore
        self.canntIgnoreUserIds = canntIgnoreUserIds


class PushRoomLedMsgEvent(ActiveRoomEvent):
    def __init__(self, activeRoom, msg, excludeUserIds=[]):
        super(PushRoomLedMsgEvent, self).__init__(activeRoom)
        self.msg = msg
        self.excludeUserIds = excludeUserIds


class SendRoomMsgEvent(ActiveRoomEvent):
    def __init__(self, activeRoom, msg, excludeUserIds, canIgnore):
        super(SendRoomMsgEvent, self).__init__(activeRoom)
        self.msg = msg
        self.canIgnore = canIgnore
        self.excludeUserIds = excludeUserIds


class SendRoomMsgToUserEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, msg):
        super(SendRoomMsgToUserEvent, self).__init__(activeRoom, roomUser)
        self.msg = msg


class LockRoomEvent(ActiveRoomEvent):
    def __init__(self, activeRoom, locked):
        super(LockRoomEvent, self).__init__(activeRoom)
        self.locked = locked


class PushRoomInfoEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser):
        super(PushRoomInfoEvent, self).__init__(activeRoom, roomUser)


class PushRoomUserListEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, listType):
        super(PushRoomUserListEvent, self).__init__(activeRoom, roomUser)
        self.listType = listType


class PushRoomUserListAllEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, pageIndex, pageNum,):
        super(PushRoomUserListAllEvent, self).__init__(activeRoom, roomUser)
        self.pageIndex = pageIndex
        self.pageNum = pageNum


class PushRoomUserListThreeEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser=None):
        super(PushRoomUserListThreeEvent, self).__init__(activeRoom, roomUser)


class PushRoomUserInfoEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, queryRoomUser, isAttention, inTheRoom):
        super(PushRoomUserInfoEvent, self).__init__(activeRoom, roomUser)
        self.queryRoomUser = queryRoomUser
        self.isAttention = isAttention
        self.inTheRoom = inTheRoom


class UserEnterRoomEvent(ActiveRoomUserEvent):
    '''
    用户进入房间事件
    '''
    def __init__(self, activeRoom, roomUser):
        super(UserEnterRoomEvent, self).__init__(activeRoom, roomUser)


class UserReconnectRoomEvent(ActiveRoomUserEvent):
    '''
    用户进入房间
    '''
    def __init__(self, activeRoom, roomUser):
        super(UserReconnectRoomEvent, self).__init__(activeRoom, roomUser)


class UserLeaveRoomEvent(ActiveRoomUserEvent):
    '''
    用户离开房间事件
    '''
    def __init__(self, activeRoom, roomUser, reason, reasonInfo=None):
        super(UserLeaveRoomEvent, self).__init__(activeRoom, roomUser)
        ## 离开原因
        self.reason = reason
        self.reasonInfo = reasonInfo


class SendTextMsgToRoomEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, msgType, msg):
        super(SendTextMsgToRoomEvent, self).__init__(activeRoom, roomUser)
        self.msgType = msgType
        self.msg = msg


class SendEmoticonEvent(ActiveRoomUserEvent):
    def __init__(self, activeRoom, roomUser, emoticon):
        super(SendEmoticonEvent, self).__init__(activeRoom, roomUser)
        self.emoticon = emoticon


