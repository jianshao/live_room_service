# -*- coding:utf-8 -*-
'''
Created on 2020年10月22日

@author: zhaojiangang
'''
import random
import time
import hashlib
import uuid

import fqparty
from fqparty.const import AdminTypes, UserLeaveMicReason, MicIds, ErrorCode, \
    SyncRoomDataTypes
from fqparty.domain.events.events import UserOnMicEvent, UserLeaveMicEvent, \
    MicDisableEvent, MicLockEvent, MicCountdownEvent, UserInviteMicEvent, \
    RoomCreateAcrossPKEvent, RoomCreateAcrossPKListEvent, RoomSponsoreAcrossPKEvent, \
    RoomAcrossPKListEvent, RoomReplyAcrossPKEvent, RoomPKSearchEvent, \
    UserOnPKLocationEvent, UserLeavePKLocationEvent, UserInvitePKLocationEvent, \
    DisablePKLocationEvent, LockPKLocationEvent, PKLocationCountdownEvent, \
    MicRoomLoadEvent, RoomUpdatePKRankEvent, MicEmoticonStartEvent, \
    MicEmoticonFinishEvent, RoomPKExpireEvent, RoomAcrossPKExpireEvent
from fqparty.domain.mic.room_across_pk import AcrossPK, RoomAcrossPK, \
    RoomAcrossPKStatus
from fqparty.domain.mic.room_manager import ActiveMicManager
from fqparty.domain.mic.room_team_pk import RoomTeamPK, RoomTeamPKStatus
from fqparty.domain.models.room import MicUserStatus, RoomMicStatus
from fqparty.servers.mic import MicServer
from tomato.core.exceptions import TTException
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog, ttbilog, strutil, timeutil
from tomato.utils.orderdedict import TTOrderedDict


class RoomMicUser(object):
    def __init__(self, roomMic, user, status):
        # 房间麦位
        self.roomMic = roomMic
        # 麦位上用户信息
        self.user = user
        # 用户麦位状态MicUserStatus
        self.status = status 
    
    @property
    def userId(self):
        return self.user.userId
    
    @property
    def micId(self):
        return self.roomMic.micId


class RoomMic(object):
    def __init__(self, activeRoom, status):
        # 所属房间
        self.activeRoom = activeRoom
        # micstatus
        self.status = status
        # 心动值
        self.heartValue = 0
        # 动画表情
        self.emoticon = None
        self.emoticonUser = None
        self.emoticonTimer = None
        self.emoticonFinishImage = None
        # 麦位
        self.micUser = None

    @property
    def micId(self):
        return self.status.micId
        
    def startEmoticon(self, user, emoticon):
        assert(not self.emoticon and self.status.userId)
        self.emoticon = emoticon
        self.emoticonUser = user
        self.emoticonTimer = TTTaskletTimer.runOnce(3, self._onEmoticonFinish)
        self.emoticonFinishImage = emoticon.gameImage[random.randint(0, len(emoticon.gameImage) - 1)]
        ttlog.info('MicEmoticonStart',
                   'emoticonId=', self.emoticon.emoticonId,
                   'emoticonFinishImage=', self.emoticonFinishImage,
                   'userId=', user.userId)

        fqparty.app.fire(MicEmoticonStartEvent(self.activeRoom, self, user, emoticon, self.emoticonFinishImage, 3))

    def _onEmoticonFinish(self):
        emoticon, self.emoticon = self.emoticon, None
        emoticonUser, self.emoticonUser = self.emoticonUser, None
        self.emoticonTimer.cancel()
        self.emoticonTimer = None
        ttlog.info('MicEmoticonFinish',
                   'emoticonId=', emoticon.emoticonId,
                   'userId=', emoticonUser.userId,
                   'finishImage=', self.emoticonFinishImage)
        
        fqparty.app.fire(MicEmoticonFinishEvent(self.activeRoom, self, emoticonUser, emoticon, self.emoticonFinishImage))


class MicRoom(object):
    '''
    活跃的房间
    '''
    def __init__(self, room, ownerUser):
        # 房间
        self.room = room
        # 房主
        self.ownerUser = ownerUser
        # 团战pk
        self.roomTeamPK = None
        # 跨房pk
        self.acrossRoomPK = None
        # 麦位
        self.micList = [RoomMic(self, RoomMicStatus(micId)) for micId in MicIds.micIDs]
        self.micMap = {mic.micId: mic for mic in self.micList}

    @property
    def roomId(self):
        return self.room.roomId

    def userHeartbeat(self, userId):
        micUser = self.findMicUser(userId)
        if micUser:
            micUser.status.heartbeatTime = timeutil.currentTimestamp()
            MicServer.micUserStatusDao.saveMicUserStatus(self.roomId, userId, micUser.status)
            ttlog.info('userHeartbeat',
                       'roomId=', self.roomId,
                       'userId=', userId)
        
    def checkInactiveMicUsers(self, timeoutSeconds):
        '''
        检查不活跃的麦位用户
        '''
        curTime = timeutil.currentTimestamp()
        for mic in self.micList:
            if mic.micUser and curTime > mic.micUser.status.heartbeatTime + timeoutSeconds:
                self.userLeaveMic(mic.micUser, UserLeaveMicReason.TIMEOUT)
        
    def _initLoad(self):
        # 初始化麦位
        roomMicStatusMap = MicServer.roomMicStatusDao.loadRoomMicStatusMap(self.roomId)
        for roomMicStatus in roomMicStatusMap.values():
            roomMic = self.findMic(roomMicStatus.micId)
            if not roomMic:
                MicServer.roomMicStatusDao.removeRoomMicStatus(self.roomId, roomMicStatus.micId)
            else:
                if roomMicStatus.userId:
                    user = MicServer.userCacheDao.loadUser(roomMicStatus.userId)
                    if not user:
                        MicServer.micUserStatusDao.removeMicUserStatus(self.roomId, roomMicStatus.userId)
                        roomMicStatus.userId = 0
                    else:
                        micUserStatus = MicServer.micUserStatusDao.loadMicUserStatus(self.roomId, roomMicStatus.userId)
                        if not micUserStatus:
                            micUserStatus = MicUserStatus(roomMicStatus.userId)
                        micUser = RoomMicUser(roomMic, user, micUserStatus)
                        roomMic.status = roomMicStatus
                        roomMic.micUser = micUser
                        micUser.roomMic = roomMic
    
        # 初始化PK
        roomTeamPKStatus = MicServer.roomTeamPKStatusDao.loadRoomTeamPKStatus(self.roomId)
        acrossRoomPKStatus = MicServer.roomAcrossPKStatusDao.loadRoomAcrossPKStatus(self.roomId)
        
        if roomTeamPKStatus:
            if not roomTeamPKStatus.isExpire():
                roomTeamPk = RoomTeamPK(self, roomTeamPKStatus)
                self.roomTeamPK = roomTeamPk
            else:
                fqparty.app.fire(RoomPKExpireEvent(self))
        
        if acrossRoomPKStatus:
            if not acrossRoomPKStatus.isExpire():
                acrossRoomPK = RoomAcrossPK(self, acrossRoomPKStatus)
                self.acrossRoomPK = acrossRoomPK
            else:
                fqparty.app.fire(RoomAcrossPKExpireEvent(self))
            
        self.updateMicsStatus()

    def start(self):
        if self.acrossRoomPK:
            self.acrossRoomPK.startPKTimer()

        if self.roomTeamPK:
            self.roomTeamPK.startPKTimer()
    
    def stop(self):
        if self.acrossRoomPK:
            self.acrossRoomPK.stopPKTimer()
            
        if self.roomTeamPK:
            self.roomTeamPK.stopPKTimer()

    def findMicUser(self, userId):
        for mic in self.micList:
            if mic.micUser and mic.micUser.userId == userId:
                return mic.micUser
        return None

    def clearMicForPK(self):
        for mic in self.micList:
            mic.status.disabled = False
            mic.status.locked = False

        ttlog.info('clearMicForPK',
                   'roomId=', self.roomId)

    def cleanMic(self, reason):
        for _, mic in self.micMap.iteritems():
            if mic.micUser:
                self.userLeaveMic(mic.micUser, reason)

    def updateMicsStatus(self):
        # 更新所有麦位状态
        roomMicStatusMap = {mic.micId: mic.status for mic in self.micList}
        MicServer.roomMicStatusDao.saveRoomMicStatusMap(self.roomId, roomMicStatusMap)

    def findAdmin(self, userId):
        return self.room.findAdmin(userId)

    def findMic(self, micId):
        return self.micMap.get(micId)
    
    def isOwner(self, userId):
        return userId == self.room.ownerUserId

    def getUserIdentity(self, userId):
        if userId == self.ownerUser.userId:
            return AdminTypes.OWNER

        admin = self.findAdmin(userId)
        if admin:
            return admin.adminType

        return AdminTypes.USER

    def findIdleMic(self):
        for _, mic in self.micMap.iteritems():
            if not mic.status.userId and mic.micId != MicIds.OWNER and not mic.status.locked:
                return mic
        return None

    def getAllAdminRoomUser(self):
        ret = []
        for userId, admin in self.room.adminMap.iteritems():
            if admin.adminType in (AdminTypes.OWNER, AdminTypes.ADMIN):
                if MicServer.roomOnlineUserListDao.existsRoomOnlineUser(self.roomId, userId) and userId != self.room.ownerUserId:
                    ret.append(userId)

        if MicServer.roomOnlineUserListDao.existsRoomOnlineUser(self.roomId, self.room.ownerUserId):
            ret.append(self.room.ownerUserId)
        return ret

    def canOpMic(self, userId):
        '''
        是否可以操作mic
        '''
        roomAdmin = self.findAdmin(userId)
        return (self.isOwner(userId)
                or (roomAdmin
                    and roomAdmin.adminType in (AdminTypes.OWNER,
                                                AdminTypes.ADMIN,
                                                AdminTypes.OFFICAL)))

    def canOpRoom(self, userId):
        roomAdmin = self.findAdmin(userId)
        return (self.isOwner(userId)
                or (roomAdmin
                    and roomAdmin.adminType in (AdminTypes.OWNER,
                                                AdminTypes.ADMIN,
                                                AdminTypes.OFFICAL)))

    def checkOnMicPermission(self, userId, micId):
        '''
        是否可以上该麦位
        '''
        # if micId != MicIds.OWNER and userId == self.room.ownerUserId:
        #     # 房主只能上房主麦
        #     raise TTException(ErrorCode.MIC_ON_NOT_OWNER, '您不能上当前麦位')

        if micId == MicIds.OWNER:
            if userId == self.room.ownerUserId:
                # 房主可以上
                return

            roomAdmin = self.findAdmin(userId)
            if (roomAdmin
                    and (roomAdmin.adminType in (AdminTypes.OWNER,
                                                 AdminTypes.ADMIN,
                                                 AdminTypes.OFFICAL))):
                # 管理员可以上
                return
            # MicIds.OWNER号麦只能房主上
            raise TTException(ErrorCode.MIC_ON_OWNER, '您不能上当前麦位')

    def buildMessageId(self):
        uuid_str = str(uuid.uuid4())
        first = hashlib.md5()
        first.update(uuid_str)
        new_str = first.hexdigest()

        second = hashlib.md5()
        second.update(new_str)
        return second.hexdigest()

    def userOnMic(self, user, mic):
        '''
        用户上麦
        '''
        self.checkOnMicPermission(user.userId, mic.micId)

        if mic.status.locked:
            # 锁麦后invite的玩家和房主可以上这个麦
            if not self.canOpMic(user.userId) and user.userId != mic.status.inviteUserId:
                raise TTException(ErrorCode.MIC_LOCKED, '锁麦之后不可以再上麦')

            self._lockMicImpl(None, mic, False)

        micUserStatus = MicUserStatus(user.userId)
        micUserStatus.micId = mic.micId
        micUserStatus.heartbeatTime = micUserStatus.onMicTime = timeutil.currentTimestamp()
        micUser = RoomMicUser(mic, user, micUserStatus)

        mic.micUser = micUser
        mic.status.userId = user.userId
        
        MicServer.roomMicStatusDao.saveRoomMicStatus(self.roomId, mic.status)
        MicServer.micUserStatusDao.saveMicUserStatus(self.roomId, user.userId, micUserStatus)
        fqparty.app.utilService.addMicUser(self.roomId, mic.micId, micUser.userId)

        # 用户上麦成功，增加5点评估积分,防黑产策略使用
        body = {'userId': user.userId, 'roomId': self.roomId, 'micId': mic.micId, 'timestamp': int(time.time())}
        data = {
            'messageId': self.buildMessageId(),
            'type': 'OnMicEvent',
            'timestamp': int(time.time()),
            'body': strutil.jsonDumps(body)
        }
        # MicServer.micMq.publish(exchange='ex_flow_message_bus', router='userOnMic', data=data)

        ttlog.info('UserOnMic ok',
                   'roomId=', self.roomId,
                   'user=', user.userId,
                   'micId=', mic.micId)
        
        fqparty.app.fire(UserOnMicEvent(self, micUser, mic))

        ttbilog.info(strutil.jsonDumps({
            'type': 'user_on_mic',
            'userId': user.userId,
            'roomId': self.roomId,
            'micId': micUserStatus.micId,
            'logTime': micUserStatus.onMicTime
        }))
        
        return micUser

    def _leaveMicImpl(self, micUser, reason):
        assert(micUser.roomMic)
        
        mic = micUser.roomMic
        mic.micUser = None
        micUser.roomMic = None
        mic.status.userId = 0
        
        MicServer.roomMicStatusDao.removeRoomMicStatus(self.roomId, mic.micId)
        MicServer.micUserStatusDao.removeMicUserStatus(self.roomId, micUser.userId)
        fqparty.app.utilService.removeMicUser(self.roomId, micUser.userId)
        
        ttlog.info('UserLeaveMic ok',
                   'roomId=', self.roomId,
                   'user=', micUser.user.userId,
                   'micId=', mic.micId,
                   'reason=', reason)

        fqparty.app.fire(UserLeaveMicEvent(self, micUser, mic, reason))

        logTime = timeutil.currentTimestamp()
        duration = logTime - micUser.status.onMicTime
        ttbilog.info(strutil.jsonDumps({
            'type': 'user_leave_mic',
            'userId': micUser.user.userId,
            'roomId': self.roomId,
            'micId': mic.micId,
            'duration': duration,
            'logTime': logTime
        }))
    
    def userLeaveMic(self, micUser, reason):
        '''
        用户下麦
        '''
        if micUser.roomMic:
            # 离开麦位
            self._leaveMicImpl(micUser, reason)
            # 离开pk
            self._checkLeavePKLocation(micUser.userId, reason)

    def sendEmoticon(self, micUser, emoticon):
        # 只有麦上的玩家可以发
        # 上一个动画表情还没结束
        if micUser.roomMic.emoticon:
            raise TTException(ErrorCode.OP_FAILED)

        micUser.roomMic.startEmoticon(micUser.user, emoticon)

        ttlog.info('sendEmoticon ok',
                   'roomId=', self.roomId,
                   'user=', micUser.userId,
                   'emoticonId=', emoticon.emoticonId)

    def inviteMic(self, inviteUserId, inviteeUserId, mic):
        '''
        邀请玩家上麦
        '''
        if not self.canOpMic(inviteUserId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        if mic.status.userId != 0:
            raise TTException(ErrorCode.MIC_NOT_IDLE)

        mic.status.inviteUserId = inviteeUserId
        mic.status.inviteRoomId = self.roomId

        MicServer.roomMicStatusDao.saveRoomMicStatus(self.roomId, mic.status)
        
        ttlog.info('InviteMic ok',
                   'roomId=', self.roomId,
                   'user=', inviteUserId,
                   'inviteUser=', inviteeUserId,
                   'inviteRoomId=', self.roomId,
                   'micId=', mic.micId)

        fqparty.app.fire(UserInviteMicEvent(self, inviteUserId, inviteeUserId, mic))

    def disableMic(self, userId, mic, disabled):
        '''
        禁麦
        @param disable: 是否禁麦
        '''
        if not self.roomTeamPK and mic.micId == MicIds.OWNER:
            raise TTException(-1, '当前麦位不支持禁麦操作')

        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        if not mic.status.disabled ^ disabled:
            return

        mic.status.disabled = disabled
        
        MicServer.roomMicStatusDao.saveRoomMicStatus(self.roomId, mic.status)
        
        ttlog.info('DisableMic ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'micId=', mic.micId,
                   'disabled=', disabled)

        fqparty.app.fire(MicDisableEvent(self, mic))

    def lockMic(self, userId, mic, locked):
        '''
        锁麦
        '''
        if not self.roomTeamPK and mic.micId == MicIds.OWNER:
            raise TTException(-1, '当前麦位不支持锁麦操作')

        if not self.canOpMic(userId):
            raise TTException(-1)

        if not mic.status.locked ^ locked:
            return

        if mic.micUser:
            self.userLeaveMic(mic.micUser, UserLeaveMicReason.MIC_LOCKED)

        self._lockMicImpl(userId, mic, locked)

    def _lockMicImpl(self, userId, mic, locked):
        mic.status.locked = locked
        
        MicServer.roomMicStatusDao.saveRoomMicStatus(self.roomId, mic.status)
        
        ttlog.info('LockMic ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'micId=', mic.micId if mic else 0,
                   'locked=', locked)

        fqparty.app.fire(MicLockEvent(self, mic))

    def countdownMic(self, userId, mic, duration):
        '''
        麦倒计时
        '''
        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        mic.status.countdownTime = int(timeutil.currentTimestamp() + duration)
        mic.status.countdownDuration = duration
        
        MicServer.roomMicStatusDao.saveRoomMicStatus(self.roomId, mic.status)
        
        ttlog.info('CountdownMic ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'micId=', mic.micId,
                   'duration=', duration)

        fqparty.app.fire(MicCountdownEvent(self, mic))

    def cancelCountdownMic(self, userId, mic):
        '''
        结束麦倒计时
        '''
        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        mic.status.countdownTime = 0
        mic.status.countdownDuration = 0
        
        ttlog.info('CancelCountdownMic ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'micId=', mic.micId)

        fqparty.app.fire(MicCountdownEvent(self, mic))

    def checkRoomPK(self, userId):
        if not self.room.guildId:
            # 当前正在PK进行中
            raise TTException(-1, '不是派对房')

        if not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, '房主和管理员才有此权限')

        if self.roomTeamPK or self.acrossRoomPK:
            # 当前正在PK进行中
            raise TTException(-1, '当前正在PK进行中')

        return True

    def checkPKUsers(self, redList, blueList):
        redUserList, blueUserList, pkUserMap = [], [], {}

        for mic in self.micList:
            if mic.micUser:
                inRed = mic.micUser.userId in redList
                inBlue = mic.micUser.userId in blueList
                if inRed and inBlue:
                    raise TTException(-1, "每人只能参队一次")
                if inRed:
                    redUserList.append(mic.micUser)
                    pkUserMap[mic.micUser.userId] = mic.micUser
                elif inBlue:
                    blueUserList.append(mic.micUser)
                    pkUserMap[mic.micUser.userId] = mic.micUser

        if not redUserList or not blueUserList:
            raise TTException(-1, "每队至少1人才可开始")

        if ttlog.isDebugEnabled():
            ttlog.debug('MicRoom.checkPKUsers',
                        'redList=', redList,
                        'blueList=', blueList,
                        'redUserList=', [mu.userId for mu in redUserList],
                        'blueUserList=', [mu.userId for mu in blueUserList],
                        'pkUserList=', [uid for uid in pkUserMap])

        return redUserList, blueUserList, pkUserMap

    def startPK(self, createUserId, redList, blueList, punishment, countdown):
        ttlog.info('MicRoom.startPK',
                   'userId=', createUserId,
                   'punishment=', punishment,
                   'punishment=', fqparty.app.keywordService.filter(punishment),
                   'redList=', redList,
                   'blueList=', blueList,
                   'roomTeamPK=', self.roomTeamPK,
                   'countdown=', countdown)

        self.checkRoomPK(createUserId)

        redList, blueList, pkUserMap = self.checkPKUsers(redList, blueList)

        roomTeamPKStatus = RoomTeamPKStatus()
        roomTeamPKStatus.startTime = timeutil.currentTimestamp()
        roomTeamPKStatus.countdown = countdown
        roomTeamPKStatus.punishment = punishment

        roomTeamPK = RoomTeamPK(self, roomTeamPKStatus)

        for i, micUser in enumerate(redList):
            loaction = MicIds.pkRedIDs[i]
            pkLocation = roomTeamPK.pkLocationMap[loaction]
            pkLocation.userId = micUser.userId
            pkLocation.micId = micUser.micId
        
        for i, micUser in enumerate(blueList):
            loaction = MicIds.pkBlueIDs[i]
            pkLocation = roomTeamPK.pkLocationMap[loaction]
            pkLocation.userId = micUser.userId
            pkLocation.micId = micUser.micId

        # 如果主持麦没有被选中 并且有人在麦上
        hostMic = self.findMic(MicIds.OWNER)
        if hostMic.micUser and hostMic.micUser.userId not in pkUserMap:
            loaction = MicIds.pkHost
            pkLocation = roomTeamPK.pkLocationMap[loaction]
            pkLocation.userId = hostMic.micUser.userId
            pkLocation.micId = hostMic.micId

        # 清空麦位的状态
        self.clearMicForPK()
        self.updateMicsStatus()

        # 没有坐着主持麦上并且没有被选中的人要下麦
        for mic in self.micList:
            if mic.micId != MicIds.OWNER and mic.micUser and mic.micUser.userId not in pkUserMap:
                self.userLeaveMic(mic.micUser, UserLeaveMicReason.ROOM_DATA_CHANGED)

        # 开始倒计时
        self.roomTeamPK = roomTeamPK
        self.roomTeamPK.startPK()

        ttlog.info('RoomPK.startPK',
                   'roomId=', self.roomId,
                   'pkUserMap=', pkUserMap)

    def endPK(self, userId=0, needPermission=0):
        ttlog.info('MicRoom.endPK',
                   'roomTeamPK=', self.roomTeamPK,
                   'userId=', userId)

        if not self.roomTeamPK:
            # 当前正在PK进行中
            raise TTException(-1, "没有PK或者PK已结束")

        if needPermission and not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, "房主和管理员才有此权限")

        roomTeamPK, self.roomTeamPK = self.roomTeamPK, None
        roomTeamPK.endPK()

        # 清空麦位的状态
        self.clearMicForPK()
        self.updateMicsStatus()

    def addPKCountdown(self, userId, duration):
        ttlog.info('ActiveRoom.addPKCountdown',
                   'userId=', userId,
                   'duration=', duration)

        if not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, "房主和管理员才有此权限")

        # 倒计时大于1分钟时允许加时，加时时间选择组件为3分钟、五分钟、十分钟
        if self.roomTeamPK.status.startTime-self.roomTeamPK.status.countdown < 60:
            raise TTException(-1, "低于1分钟不支持加时")

        # 开始PK时间与续时的总时间之和不能高于90分钟
        if self.roomTeamPK.status.countdown+duration > 5400:
            raise TTException(-1, "pk总时间之和不能超过90分钟")

        if duration not in [180, 300, 600]:
            raise TTException(-1, "加时不对")

        # 新的倒计时时间
        self.roomTeamPK.addPKCountdown(duration)

    def checkOnPKLocationPermission(self, userId, location):
        '''
        是否可以上该pk的位置
        '''
        if location == MicIds.pkHost:
            if userId == self.room.ownerUserId:
                # 房主可以上
                return

            roomAdmin = self.findAdmin(userId)
            if roomAdmin and (roomAdmin.adminType in (AdminTypes.OWNER,
                                                      AdminTypes.ADMIN,
                                                      AdminTypes.OFFICAL)):
                # 管理员可以上
                return
            # hostLocationID麦只能房主上
            raise TTException(ErrorCode.MIC_ON_OWNER, '您不能上当前麦位')

    def joinPKLocation(self, user, pkLocation, mic):
        '''
        用户上麦
        '''
        self.checkOnPKLocationPermission(user.userId, pkLocation.location)

        if not self.roomTeamPK.canJoin(user.userId, pkLocation.location):
            raise TTException(-1, '您已在红/蓝队中获得了pk值，不能切换队伍')

        if pkLocation.locked:
            # 锁麦后invite的玩家和房主可以上这个麦
            if not self.canOpMic(user.userId) and user.userId != pkLocation.inviteUserId:
                raise TTException(ErrorCode.MIC_LOCKED, '锁麦之后不可以再上麦')

            self._lockPKLocationImpl(None, pkLocation, False)

        self.userOnMic(user, mic)
        
        pkLocation.userId = user.userId
        pkLocation.micId = mic.micId
        
        ttlog.info('joinPKLocation ok',
                   'roomId=', self.roomId,
                   'user=', user.userId,
                   'location=', pkLocation.location,
                   'micId=', mic.micId)

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)
        fqparty.app.fire(UserOnPKLocationEvent(self, user.userId, pkLocation))

        # 如果上麦时有pk 要推送一下更新pk值
        if self.roomTeamPK.getPKValue(user.userId):
            fqparty.app.fire(RoomUpdatePKRankEvent(self))

    def _leavePKLocation(self, pkLocation, reason):
        userId, micId = pkLocation.userId, pkLocation.micId
        pkLocation.userId = 0
        pkLocation.micId = 0
        
        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)

        ttlog.info('leavePKLocation ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'micId=', micId,
                   'location=', pkLocation.location,
                   'reason=', reason)
        
        fqparty.app.fire(UserLeavePKLocationEvent(self, userId, pkLocation, reason))

        try:
            if sum([1 if pkLocation.userId else 0 for pkLocation in self.roomTeamPK.pkLocationList if
                    pkLocation.location != MicIds.pkHost]) == 0:
                # 没有人结束pk
                self.endPK()
        except:
            ttlog.error('leavePKLocation.endPK error',
                        'roomId=', self.roomId,
                        'pkUsers=', [(pkLocation.location, pkLocation.userId)
                                     for pkLocation in self.roomTeamPK.pkLocationList],
                        'redPKMap=', self.roomTeamPK.status.redPKMap,
                        'bluePKMap=', self.roomTeamPK.status.bluePKMap)
    
    def _checkLeavePKLocation(self, userId, reason):
        if self.roomTeamPK:
            pkLocation = self.roomTeamPK.getPKLocationByUserId(userId)
            if pkLocation:
                self._leavePKLocation(pkLocation, reason)

    def leavePKLocation(self, micUser, reason):
        '''
        用户下麦
        '''
        pkLocation = self.roomTeamPK.getPKLocationByUserId(micUser.userId)
        if pkLocation:
            # 先下麦
            self._leaveMicImpl(micUser, reason)
            # 下pk
            self._leavePKLocation(pkLocation, reason)

    def invitePKLocation(self, userId, inviteeUserId, pkLocation):
        '''
        邀请玩家上麦
        '''
        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        pkLocation.inviteUserId = inviteeUserId
        pkLocation.inviteRoomId = self.roomId

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)
        ttlog.info('invitePKLocation ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'inviteUser=', inviteeUserId,
                   'inviteRoomId=', self.roomId,
                   'location=', pkLocation.location)

        fqparty.app.fire(UserInvitePKLocationEvent(self, userId, inviteeUserId, pkLocation))

    def disablePKLocation(self, userId, pkLocation, disabled):
        '''
        禁麦
        @param disable: 是否禁麦
        '''
        if pkLocation.location == MicIds.pkHost:
            raise TTException(-1, '当前麦位不支持禁麦操作')

        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        if not pkLocation.disabled ^ disabled:
            return

        pkLocation.disabled = disabled

        if pkLocation.userId != 0:
            roomMic = self.findMic(pkLocation.micId)
            self.disableMic(userId, roomMic, disabled)

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)

        fqparty.app.fire(DisablePKLocationEvent(self, pkLocation))

    def lockPKLocation(self, userId, pkLocation, locked):
        '''
        锁麦
        '''
        if pkLocation.location == MicIds.pkHost:
            raise TTException(-1, '当前麦位不支持锁麦操作')

        if not self.canOpMic(userId):
            raise TTException(-1)

        if not pkLocation.locked ^ locked:
            return

        if pkLocation.userId != 0:
            micUser = self.findMicUser(pkLocation.userId)
            if micUser:
                self.leavePKLocation(micUser, UserLeaveMicReason.MIC_LOCKED)

        self._lockPKLocationImpl(userId, pkLocation, locked)

    def _lockPKLocationImpl(self, userId, pkLocation, locked):

        pkLocation.locked = locked

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)

        ttlog.info('LockPKLocation ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'location=', pkLocation.location if pkLocation else 0,
                   'locked=', locked)

        fqparty.app.fire(LockPKLocationEvent(self, pkLocation))

    def countdownPKLocation(self, userId, pkLocation, duration):
        '''
        麦倒计时
        '''
        # 只有房主和管理员此操作
        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        pkLocation.countdownTime = timeutil.currentTimestamp()
        pkLocation.countdownDuration = duration

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)

        ttlog.info('countdownPKLocation ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'location=', pkLocation.location,
                   'duration=', duration)

        fqparty.app.fire(PKLocationCountdownEvent(self, pkLocation))

    def cancelCountdownPKLocation(self, userId, pkLocation):
        '''
        结束麦倒计时
        '''
        # 只有房主和管理员此操作
        if not self.canOpMic(userId):
            raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

        pkLocation.countdownTime = 0
        pkLocation.countdownDuration = 0

        MicServer.roomPKLocationDao.saveRoomPKLocation(self.roomId, pkLocation)
        ttlog.info('cancelCountdownPKLocation ok',
                   'roomId=', self.roomId,
                   'user=', userId,
                   'location=', pkLocation.location)

        fqparty.app.fire(PKLocationCountdownEvent(self, pkLocation))

    def notifyRoomAcrossPKStart(self, acrossPKData, pkRoomInfo):
        '''通知本房间pk开始'''
        if self.roomTeamPK or self.acrossRoomPK:
            # 当前正在PK进行中
            raise TTException(-1, "当前正在PK进行中")

        acrossPK = AcrossPK()
        acrossPK.fromJson(acrossPKData)

        self.startAcrossPK(acrossPK, pkRoomInfo)

    def innerStartAcrossPK(self, createRoom, creatRoomOwnerUser, pkRoom, pkRoomOwnerUser, punishment, countdown, createTime):
        ttlog.info('ActiveRoom.innerStartAcrossPK',
                   'createRoomId=', createRoom.roomId,
                   'pkRoomId=', pkRoom.roomId,
                   'createTime=', createTime,
                   'punishment=', punishment,
                   'countdown=', countdown)

        acrossPK = AcrossPK(createRoom.roomId, createRoom.prettyRoomId, pkRoom.roomId, punishment, createTime,
                            countdown, createRoom.roomName,  creatRoomOwnerUser.nickname, creatRoomOwnerUser.avatar)

        acrossRoomPKStatus = RoomAcrossPKStatus(acrossPK, timeutil.currentTimestamp())
        acrossRoomPKStatus.pkRoomName = pkRoom.roomName
        acrossRoomPKStatus.pkUserName = pkRoomOwnerUser.nickname
        acrossRoomPKStatus.pkUserAvater = pkRoomOwnerUser.avatar

        self.acrossRoomPK = RoomAcrossPK(self, acrossRoomPKStatus)
        self.acrossRoomPK.startPK()

    def startAcrossPK(self, acrossPK, pkRoomInfo):
        ttlog.info('ActiveRoom.startAcrossPK',
                   'roomId=', self.roomId,
                   'acrossPK=', acrossPK.toJson(),
                   'pkRoomInfo=', pkRoomInfo)

        acrossRoomPKStatus = RoomAcrossPKStatus(acrossPK, timeutil.currentTimestamp())
        acrossRoomPKStatus.pkRoomName = pkRoomInfo['roomName']
        acrossRoomPKStatus.pkUserName = pkRoomInfo['name']
        acrossRoomPKStatus.pkUserAvater = pkRoomInfo['avatar']

        self.acrossRoomPK = RoomAcrossPK(self, acrossRoomPKStatus)
        self.acrossRoomPK.startPK()

    def endAcrossPK(self):
        ttlog.info('ActiveRoom.endAcrossPK',
                   'roomId=', self.roomId)

        if not self.acrossRoomPK:
            # 当前正在PK进行中
            raise TTException(-1, "没有PK或者PK已结束")

        acrossRoomPK, self.acrossRoomPK = self.acrossRoomPK, None
        acrossRoomPK.endPK()

    def updatePKRoomData(self, pkMap, contributeMap):
        '''同步pk房间的数据'''
        if self.acrossRoomPK:
            self.acrossRoomPK.updatePKRoomData(pkMap, contributeMap)

    def acorssPKingInfo(self, userId):
        '''pk中pk的数据'''
        ttlog.info('ActiveRoom.acorssPKingInfo',
                   'userId=', userId,
                   'roomId=', self.roomId)
        # if self.acrossRoomPK:
        #     fqparty.app.fire(RoomAcrossPKingDataEvent(self, userId))

    def createAcrossPK(self, userId, punishment, countdown):
        ttlog.info('ActiveRoom.createAcrosspks',
                   'userId=', userId,
                   'roomId=', self.roomId,
                   'punishment=', punishment,
                   'countdown=', countdown)

        self.checkRoomPK(userId)

        createTime = timeutil.currentTimestamp()
        acrossPK = AcrossPK(self.roomId, self.room.prettyRoomId, None, punishment, createTime, countdown,
                            self.room.roomName, self.ownerUser.nickname, self.ownerUser.avatar)
        fqparty.app.utilService.setCreateAcrossPK(self.roomId, acrossPK.toJson())

        fqparty.app.fire(RoomCreateAcrossPKEvent(self, userId, acrossPK))

    def cancelCreateAcrossPK(self, userId):
        ttlog.info('ActiveRoom.cancelCreateAcrossPK',
                   'userId=', userId,
                   'roomId=', self.roomId)

        if not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, "房主和管理员才有此权限")

        if not fqparty.app.utilService.getCreateAcrossPK(self.roomId):
            # 只有房主和管理员可以pk
            raise TTException(-1, "没有创建过pk")

        fqparty.app.utilService.delCreateAcrossPK(self.roomId)

        fqparty.app.fire(RoomCreateAcrossPKEvent(self, userId, None, 1))

    def createAcrossPKList(self, userId):
        ttlog.info('ActiveRoom.createAcrossPKList',
                   'userId=', userId,
                   'roomId=', self.roomId)

        createAcrossPKList = []
        datas = fqparty.app.utilService.getCreateAcrossPKs()
        for _roomKey, data in datas.iteritems():
            acrossPK = AcrossPK().fromJson(data)
            createAcrossPKList.append(acrossPK)

        fqparty.app.fire(RoomCreateAcrossPKListEvent(self, userId, createAcrossPKList))

    def loadSponsoredAcrossPKData(self, userId=None):
        # load 被发起的pk
        sponsoredAcrossPKList = []
        datas = fqparty.app.utilService.getAllSponsoredAcrossPK(self.roomId)
        for _roomKey, data in datas.iteritems():
            acrossPK = AcrossPK().fromJson(data)

            if acrossPK.duration <= 0:
                fqparty.app.utilService.clearExpireAcrossPK(acrossPK.pkRoomId, acrossPK.createRoomId)
                ttlog.info('ActiveRoom.loadSponsoredAcrossPKData remove',
                           'data=', data)
            else:
                sponsoredAcrossPKList.append(acrossPK)

        # if not sponsoredAcrossPKList:
        #     return

        if userId:
            fqparty.app.fire(RoomAcrossPKListEvent(self, userId, sponsoredAcrossPKList))
        else:
            # 只推送给房间管理员
            userIds = self.getAllAdminRoomUser()
            for userId in userIds:
                fqparty.app.fire(RoomAcrossPKListEvent(self, userId, sponsoredAcrossPKList))

    def _getSponsoredAcrossPK(self, roomId, pkRoomId):
        data = fqparty.app.utilService.getSponsoredAcrossPK(roomId, pkRoomId)
        if data:
            if timeutil.currentTimestamp() - data['createTime'] > 60:
                fqparty.app.utilService.clearExpireAcrossPK(data['pkRoomId'], data['createRoomId'])
                ttlog.info('ActiveRoom._getSponsoredAcrossPK remove',
                           'data=', data)
                return None

        return data

    def sponsoreAcrossPK(self, userId, pkRoomId, punishment, countdown):
        '''本房间发起pk'''
        ttlog.info('ActiveRoom.sponsoreAcrossPK',
                   'userId=', userId,
                   'roomId=', self.roomId,
                   'pkRoomId=', pkRoomId,
                   'punishment=', punishment,
                   'countdown=', countdown)

        self.checkRoomPK(userId)

        if self._getSponsoredAcrossPK(pkRoomId, self.roomId):
            raise TTException(-1, "已对该房间发起过pk，不可再发起")

        if self._getSponsoredAcrossPK(self.roomId, pkRoomId):
            raise TTException(-1, "该房间对本房间发起过pk，不可再发起")

        createTime = timeutil.currentTimestamp()
        acrossPK = AcrossPK(self.roomId, self.room.prettyRoomId, pkRoomId, punishment, createTime, countdown,
                            self.room.roomName, self.ownerUser.nickname, self.ownerUser.avatar)
        # 被发起的列表添加数据
        fqparty.app.utilService.setSponsoredAcrossPK(pkRoomId, self.roomId, acrossPK.toJson())

        fqparty.app.fire(RoomSponsoreAcrossPKEvent(self, userId, acrossPK))

    def invitePKList(self, userId):
        '''房间内的pk列表'''
        self.loadSponsoredAcrossPKData(userId)

    def notifyRoomSponsored(self):
        '''通知本房间被发起pk 客户端推送pk列表'''

        # 如果该房间有pk 不推送
        if self.roomTeamPK or self.acrossRoomPK:
            return

        self.loadSponsoredAcrossPKData()

    def acceptAcrossPK(self, userId, targetRoomId):
        '''本房间接受pk'''
        ttlog.info('ActiveRoom.acceptAcrossPK',
                   'userId=', userId,
                   'roomId=', self.roomId,
                   'targetRoomId=', targetRoomId)

        if not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, "房主和管理员才有此权限")

        if self.roomTeamPK or self.acrossRoomPK:
            # 只有房主和管理员可以pk
            raise TTException(-1, "本房间已有pk")

        # 如果接受的是别人创建的pk
        data = fqparty.app.utilService.getCreateAcrossPK(targetRoomId)
        if data:
            acrossPK = AcrossPK().fromJson(data)
            acrossPK.pkRoomId = self.roomId
            fqparty.app.utilService.delCreateAcrossPK(targetRoomId)
        else:
            # 接受的是别人对我发起的
            data = self._getSponsoredAcrossPK(self.roomId, targetRoomId)
            if not data:
                raise TTException(-1, "没有该pk或者已过期")

            acrossPK = AcrossPK().fromJson(data)

        fqparty.app.fire(RoomReplyAcrossPKEvent(self, userId, targetRoomId, 1))

        pkRoomInfo = {
            "name": self.ownerUser.nickname,
            "roomName": self.room.roomName,
            "avatar": self.ownerUser.avatar,
        }

        return True, acrossPK, pkRoomInfo

    def refusedAcrossPK(self, userId, refusedRoomId):
        '''拒绝发起的pk邀请'''

        if not self.canOpRoom(userId):
            # 只有房主和管理员可以pk
            raise TTException(ErrorCode.NOT_ADMIN_OP_ROOM, "房主和管理员才有此权限")

        # if not self._getSponsoredAcrossPK(self.roomId, refusedRoomId):
        #     raise TTException(-1, "没有pk邀请或者pk已过期")

        fqparty.app.utilService.clearExpireAcrossPK(self.roomId, refusedRoomId)
        fqparty.app.fire(RoomReplyAcrossPKEvent(self, userId, refusedRoomId, 2))

    def searchRoom(self, userId, searchRoom, searchRoomOwnerUser):
        ttlog.info('ActiveRoom.searchRoom',
                   'userId=', userId,
                   'searchId=', searchRoom.roomId,
                   'roomId=', self.roomId)

        status = 1 # 状态 1普通房间，没有创建或发起过pk 2-自己房间创建的pk 3-别人房间创建的pk 4-该房间对我发起的pk 5我对该房间发起过pk
        # 该房间是否创建过pk
        data = fqparty.app.utilService.getCreateAcrossPK(searchRoom.roomId)
        if data:
            status = 2 if searchRoom.roomId == self.roomId else 3
        else:
            # 该房间是否对本房间发起的
            data = self._getSponsoredAcrossPK(self.roomId, searchRoom.roomId)
            if data:
                status = 4
            else:
                # 本房间对该房间发起过pk
                data = self._getSponsoredAcrossPK(searchRoom.roomId, self.roomId)
                if data:
                    status = 5

        acrossPK = AcrossPK().fromJson(data) if data else None

        fqparty.app.fire(RoomPKSearchEvent(self, userId, searchRoom, searchRoomOwnerUser, acrossPK, status))

    def pushRoomMsg(self, msg):
        ttlog.info('PushRoomMsg ok',
                   'roomId=', self.roomId,
                   'msg=', msg)

        if self.roomTeamPK:
            self.roomTeamPK.sendGift(msg)
        if self.acrossRoomPK:
            self.acrossRoomPK.sendGift(msg)

    def updateRoomData(self, room, dataType):
        # 更新room数据
        oldRoom = self.room

        if dataType == SyncRoomDataTypes.MODE and oldRoom.roomType.parentId == 2:
            self.cleanMic(UserLeaveMicReason.ROOM_DATA_CHANGED)
        elif self.room.roomType.typeId == 2:
            self.cleanMic(UserLeaveMicReason.ROOM_DATA_CHANGED)

        self.room = room

        if oldRoom.roomType != room.roomType or oldRoom.guildId != room.guildId:
            # 房间类型变化
            fqparty.app.utilService.removeRoomFromRoomTypeList(oldRoom.roomId, oldRoom.guildId, oldRoom.roomType.typeId)
            fqparty.app.utilService.addRoomToRoomTypeList(room.roomId, room.guildId, room.roomType.typeId)

        ttlog.info('UpdateRoomData ok',
                   'roomId=', self.roomId,
                   'dataType=', dataType)

    def banRoom(self, operator, reasonInfo):
        ttlog.info('banRoom ok',
                   'roomId=', self.roomId,
                   'operator=', operator,
                   'reasonInfo=', reasonInfo)

        if self.roomTeamPK:
            self.endPK()

        self.cleanMic(UserLeaveMicReason.ROOM_DATA_CHANGED)


class ActiveMicManagerImpl(ActiveMicManager):
    def __init__(self):
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
        room = MicServer.roomDao.loadRoom(roomId)
        if not room:
            raise TTException(ErrorCode.ROOM_NOT_EXISTS)

        if user and room.ownerUserId == user.userId:
            ownerUser = user
        else:
            ownerUser = MicServer.userDao.loadUser(room.ownerUserId)
            if not ownerUser:
                raise TTException(ErrorCode.ROOM_NOT_EXISTS)

        return MicRoom(room, ownerUser)


