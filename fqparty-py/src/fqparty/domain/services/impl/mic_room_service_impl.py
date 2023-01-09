# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''

import time
from fqparty import router
import fqparty
from fqparty.const import UserLeaveMicReason, ErrorCode, MicIds
from fqparty.domain.events.events import MicRoomRemoveEvent, RoomDisabledMsgEvent, MicRoomLoadEvent
from fqparty.domain.models.room import RoomStatus
from fqparty.domain.services.mic_room_service import MicRoomService
from fqparty.proxy.mic import mic_remote_proxy
from fqparty.proxy.room import room_remote_proxy
from fqparty.servers.mic import MicServer
from fqparty.utils import time_utils
from tomato.config import configure
from tomato.core.exceptions import TTException
from tomato.core.lock import TTKeyLock
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog, strutil


class MicRoomServiceImpl(MicRoomService):
    def __init__(self):
        # 房间锁
        self._roomLock = TTKeyLock()
        # 房间协议
        TTTaskletTimer.runForever(5, self._checkActiveRoom)
        TTTaskletTimer.runForever(10, self._checkInactiveMicUser)

    def _checkInactiveMicUser(self):
        activeRoomMap = MicServer.activeRoomManager.getActiveRoomMap()
        roomIds = set(activeRoomMap.keys())

        if ttlog.isDebugEnabled():
            ttlog.debug('CheckInactiveMicUser',
                        'roomIds=', roomIds)

        timeouts = configure.loadJson('server.fqparty.global', {}).get('timeouts', {})
        offlineTimeout = timeouts.get('offlineTimeout', 30)
        
        for roomId in roomIds:
            with self._roomLock.lock(roomId):
                micRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
                if micRoom:
                    micRoom.checkInactiveMicUsers(offlineTimeout + 10)

    def _checkActiveRoom(self):
        '''5s检查一次，踢出没有pk的没人的房间'''
        micRoomMap = MicServer.activeRoomManager.getActiveRoomMap()
        roomIds = set(micRoomMap.keys())

        if ttlog.isDebugEnabled():
            ttlog.debug('CheckActiveRoom',
                        'roomIds=', roomIds)

        for roomId in roomIds:
            self.removeMicRoom(roomId)

    def _ensureRoomMic(self, activeRoom, micId):
        mic = activeRoom.findMic(micId)
        if not mic:
            raise TTException(ErrorCode.UNKNOWN_MIC, '麦位错误')
        return mic

    def _ensureRoomPKLocation(self, activeRoom, location):
        if activeRoom.roomTeamPK:
            pkLocation = activeRoom.roomTeamPK.getPKLocation(location)
            if not pkLocation:
                raise TTException(ErrorCode.UNKNOWN_MIC, '麦位错误')

            return pkLocation

        raise TTException(ErrorCode.UNKNOWN_MIC, 'pk结束')

    def _ensureActiveRoom(self, roomId, user=None):
        activeRoom, isLoad = MicServer.activeRoomManager.findOrLoadActiveRoom(roomId, user)
        if not activeRoom:
            raise TTException(ErrorCode.ROOM_NOT_EXISTS, '房间不存在')
        if isLoad:
            activeRoom._initLoad()
            activeRoom.start()
            fqparty.app.fire(MicRoomLoadEvent(activeRoom))
        return activeRoom

    def _removeActiveRoom(self, roomId):
        totalUserCount = MicServer.roomOnlineUserListDao.getRoomOnlineUserCount(roomId)
        if totalUserCount == 0:
            micRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
            if micRoom:
                micRoom.stop()
                fqparty.app.fire(MicRoomRemoveEvent(micRoom))
            MicServer.activeRoomManager.removeActiveRoom(roomId)

            ttlog.info('RemoveActiveRoom ok',
                       'roomId=', roomId,
                       'totalUserCount=', totalUserCount)

    def loadMicRoom(self, roomId):
        with self._roomLock.lock(roomId):
            MicServer.activeRoomManager.findOrLoadActiveRoom(roomId)

    def removeMicRoom(self, roomId):
        with self._roomLock.lock(roomId):
            self._removeActiveRoom(roomId)

    def findActiveRoom(self, roomId):
        return MicServer.activeRoomManager.findActiveRoom(roomId)
    
    def userHeartbeat(self, roomId, userId):
        '''
        用户心跳
        '''
        activeRoom = self.findActiveRoom(roomId)
        if activeRoom:
            activeRoom.userHeartbeat(userId)
    
    def userOnMic(self, roomId, user, micId):
        with self._roomLock.lock(roomId):
            # 加载活跃房间
            activeRoom = self._ensureActiveRoom(roomId, user)
            if activeRoom.roomTeamPK:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您的版本过低PK进行中不支持该操作')

            micUser = activeRoom.findMicUser(user.userId)
            if micUser:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您已经在麦上')

            if micId == MicIds.RANDOM:
                # 自动选麦
                mic = activeRoom.findIdleMic()
                if not mic:
                    raise TTException(ErrorCode.NO_IDLE_MIC, '麦位上无空缺，请稍后再试')
            else:
                mic = self._ensureRoomMic(activeRoom, micId)
                if mic.status.userId != 0:
                    raise TTException(ErrorCode.NO_IDLE_MIC, '麦位上无空缺，请稍后再试')

            activeRoom.userOnMic(user, mic)

    def userLeaveMic(self, roomId, userId, reason, force=False):
        with self._roomLock.lock(roomId):
            # 加载活跃房间
            activeRoom = self._ensureActiveRoom(roomId)
            if not force and activeRoom.roomTeamPK:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您的版本过低PK进行中不支持该操作')

            micUser = activeRoom.findMicUser(userId)
            if micUser:
                activeRoom.userLeaveMic(micUser, reason)

    def lockMic(self, roomId, userId, micId, locked):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if activeRoom.roomTeamPK:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您的版本过低PK进行中不支持该操作')

            mic = self._ensureRoomMic(activeRoom, micId)
            activeRoom.lockMic(userId, mic, locked)
            return mic

    def disableMic(self, roomId, userId, micId, disabled):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if activeRoom.roomTeamPK:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您的版本过低PK进行中不支持该操作')

            mic = self._ensureRoomMic(activeRoom, micId)
            activeRoom.disableMic(userId, mic, disabled)

    def inviteMic(self, roomId, userId, inviteeUserId, micId, cancel):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if activeRoom.roomTeamPK:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您的版本过低PK进行中不支持该操作')

            # 只有房主和管理员可以抱麦
            if not activeRoom.canOpMic(userId):
                # 只有房主和管理员可以抱麦
                raise TTException(ErrorCode.NOT_ADMIN_OP_MIC)

            if cancel:
                micUser = activeRoom.findMicUser(inviteeUserId)
                if micUser:
                    activeRoom.userLeaveMic(micUser, UserLeaveMicReason.USER_INVITE)
            else:
                if micId == MicIds.RANDOM:
                    mic = activeRoom.findIdleMic()
                    if not mic:
                        raise TTException(ErrorCode.NO_IDLE_MIC, '麦位已经被占用')
                else:
                    mic = self._ensureRoomMic(activeRoom, micId)

                activeRoom.inviteMic(userId, inviteeUserId, mic)

    def countdownMic(self, roomId, userId, micId, duration):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            mic = self._ensureRoomMic(activeRoom, micId)
            activeRoom.countdownMic(userId, mic, duration)

    def cancelCountdownMic(self, roomId, userId, micId):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            mic = self._ensureRoomMic(activeRoom, micId)
            activeRoom.cancelCountdownMic(userId, mic)

    def startPK(self, roomId, createUserId, redList, blueList, punishment, countdown):
        if len(punishment) > 20:
            raise TTException(-1, "惩罚最多10个字哦")

        if fqparty.app.keywordService.filter(punishment) != punishment:
            raise TTException(-1, "当前惩罚包含色情或敏感字字符")

        if countdown < 60 or countdown > 3600:
            raise TTException(-1, "时间设置不对")

        if len(redList) > 4 or len(redList) == 0 or len(blueList) > 4 or len(blueList) == 0:
            raise TTException(-1, "人数错误")

        date = time_utils.formatTimeDay()
        isCheckOpen = self._checkPKOpen(createUserId, date)

        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.startPK(createUserId, redList, blueList, punishment, int(countdown))
            if isCheckOpen:
                fqparty.app.utilService.incrPKOpenNum(date, createUserId)

    def endPK(self, roomId, userId):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.endPK(userId, 1)

    def innerEndPK(self, roomId):
        with self._roomLock.lock(roomId):
            activeRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
            if activeRoom:
                activeRoom.endPK()
            ttlog.warn('innerEndPK error', 'roomId=', roomId)

    def joinPKLocation(self, roomId, user, location):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if not activeRoom.roomTeamPK:
                raise TTException(-1, '该pk已结束')

            micUser = activeRoom.findMicUser(user.userId)
            if micUser:
                raise TTException(ErrorCode.ALREADY_ON_MIC, '您已经在麦上')

            pkLocation = self._ensureRoomPKLocation(activeRoom, location)
            if pkLocation.micId != 0:
                raise TTException(ErrorCode.NO_IDLE_MIC, '麦位上无空缺，请稍后再试')

            # 如果要上主持位置 如果999麦上没有人 要选999麦
            mic = None
            if location == MicIds.pkHost:
                hostMic = self._ensureRoomMic(activeRoom, MicIds.OWNER)
                if not hostMic.micUser:
                    mic = hostMic

            if not mic:
                # 自动选麦
                mic = activeRoom.findIdleMic()

            if not mic:
                raise TTException(ErrorCode.NO_IDLE_MIC, '麦位上无空缺，请稍后再试')

            activeRoom.joinPKLocation(user, pkLocation, mic)
            return mic.micId

    def leavePKLocation(self, roomId, userId, reason):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            micUser = activeRoom.findMicUser(userId)
            if micUser:
                activeRoom.leavePKLocation(micUser, reason)

    def lockPKLocation(self, roomId, userId, location, locked):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            pkLocation = self._ensureRoomPKLocation(activeRoom, location)
            activeRoom.lockPKLocation(userId, pkLocation, locked)

    def disablePKLocation(self, roomId, userId, location, disabled):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            pkLocation = self._ensureRoomPKLocation(activeRoom, location)
            activeRoom.disablePKLocation(userId, pkLocation, disabled)

    def invitePKLocation(self, roomId, userId, inviteeUserId, location, cancel):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if cancel:
                micUser = activeRoom.findMicUser(inviteeUserId)
                if micUser:
                    activeRoom.leavePKLocation(micUser, UserLeaveMicReason.USER_INVITE)
            else:
                pkLocation = self._ensureRoomPKLocation(activeRoom, location)
                if pkLocation.userId != 0:
                    raise TTException(ErrorCode.NO_IDLE_MIC, '麦位已经被占用')

                activeRoom.invitePKLocation(userId, inviteeUserId, pkLocation)

    def countdownPKLocation(self, roomId, userId, location, duration):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            pkLocation = self._ensureRoomPKLocation(activeRoom, location)
            activeRoom.countdownPKLocation(userId, pkLocation, duration)

    def cancelCountdownPKLocation(self, roomId, userId, location):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            pkLocation = self._ensureRoomPKLocation(activeRoom, location)
            activeRoom.cancelCountdownPKLocation(userId, pkLocation)

    def addPKCountdown(self, roomId, userId, duration):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.addPKCountdown(userId, int(duration))

    def updatePKRoomData(self, roomId, pkMap, contributeMap):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.updatePKRoomData(pkMap, contributeMap)

    def notifyRoomAcrossPKStart(self, roomId, acrossPKData, pkRoomInfo):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.notifyRoomAcrossPKStart(acrossPKData, pkRoomInfo)

    def acorssPKingInfo(self, roomId, userId):
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            activeRoom.acorssPKingInfo(userId)

    def innerEndAcrossPK(self, roomId):
        with self._roomLock.lock(roomId):
            activeRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
            if activeRoom:
                activeRoom.endAcrossPK()

            ttlog.info('innerEndAcrossPK ok', 'roomId=', roomId)

    def innerStartAcrossPK(self, roomId, createRoomId, pkRoomId, punishment, countdown):
        if createRoomId == pkRoomId:
            raise TTException(-1, "相同房间不可以发起pk")

        if len(punishment) > 20:
            raise TTException(-1, "惩罚最多10个字哦")

        if fqparty.app.keywordService.filter(punishment) != punishment:
            raise TTException(-1, "当前惩罚包含色情或敏感字字符")

        if countdown < 60 or countdown > 3600:
            raise TTException(-1, "时间设置不对, 必须在60-3600秒之间")

        createRoom = MicServer.roomDao.loadRoom(roomId)
        if not createRoom or not createRoom.guildId:
            raise TTException(-1, str(createRoomId) + "不是派对房")
        
        creatRoomOwnerUser = MicServer.userDao.loadUser(createRoom.ownerUserId)

        pkRoom = MicServer.roomDao.loadRoom(roomId)
        if not pkRoom or not pkRoom.guildId:
            raise TTException(-1, str(pkRoomId) + "不是派对房")
        
        pkRoomOwnerUser = MicServer.userDao.loadUser(pkRoom.ownerUserId)

        createTime = time_utils.getCurrentTimestamp()
        with self._roomLock.lock(roomId):
            activeRoom = self._ensureActiveRoom(roomId)
            if activeRoom.acrossRoomPK:
                activeRoom.endAcrossPK()
            activeRoom.innerStartAcrossPK(createRoom, creatRoomOwnerUser, pkRoom, pkRoomOwnerUser, punishment, countdown, createTime)

    def notifyRoomSponsored(self, roomId):
        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.notifyRoomSponsored()

    def invitePKList(self, roomId, userId):
        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.invitePKList(userId)

    def createAcrossPK(self, roomId, userId, punishment, countdown):
        if len(punishment) > 20:
            raise TTException(-1, "惩罚最多10个字哦")

        if fqparty.app.keywordService.filter(punishment) != punishment:
            raise TTException(-1, "当前惩罚包含色情或敏感字字符")

        if countdown < 60 or countdown > 3600:
            raise TTException(-1, "时间设置不对")

        if fqparty.app.utilService.getCreateAcrossPK(roomId):
            raise TTException(-1, "已创建过pk，不可再创建")

        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.createAcrossPK(userId, punishment, countdown)

    def cancelCreateAcrossPK(self, roomId, userId):
        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.cancelCreateAcrossPK(userId)

    def createAcorssPKList(self, roomId, userId):
        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.createAcrossPKList(userId)

    def sponsoreAcrossPK(self, roomId, userId, pkRoomId, punishment, countdown):
        if pkRoomId == roomId:
            raise TTException(-1, "不可对本房间发起pk")

        if len(punishment) > 20:
            raise TTException(-1, "惩罚最多10个字哦")

        if fqparty.app.keywordService.filter(punishment) != punishment:
            raise TTException(-1, "当前惩罚包含色情或敏感字字符")

        if countdown < 60 or countdown > 3600:
            raise TTException(-1, "时间设置不对")

        room = MicServer.roomDao.loadRoom(pkRoomId)
        if not room or not room.guildId:
            raise TTException(-1, "不可以对非派对房发起pk")

        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.sponsoreAcrossPK(userId, pkRoomId, punishment, countdown)

        # 通知被发起的房间
        micRoom = MicServer.activeRoomManager.findActiveRoom(pkRoomId)
        if micRoom:
            with self._roomLock.lock(roomId):
                micRoom.notifyRoomSponsored()
        elif router.choiceMicServerForUser(roomId) != router.choiceMicServerForUser(pkRoomId):
            mic_remote_proxy.notifyRoomSponsored(pkRoomId)

    def acceptAcrossPK(self, roomId, userId, pkRoomId):
        room = MicServer.roomDao.loadRoom(pkRoomId)
        if not room or not room.guildId:
            raise TTException(-1, "该房间已经不是派对房，不可接受pk")

        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            accept, acrossPK, pkRoomInfo = micRoom.acceptAcrossPK(userId, pkRoomId)

            if accept:
                # 通知开始pk的房间
                serverId = router.choiceMicServerForUser(roomId)
                if serverId == router.choiceMicServerForUser(pkRoomId):
                    self.notifyRoomAcrossPKStart(pkRoomId, acrossPK.toJson(), pkRoomInfo)
                else:
                    ec, info = mic_remote_proxy.notifyRoomAcrossPKStart(pkRoomId, acrossPK.toJson(), pkRoomInfo)
                    if ec != 0:
                        raise TTException(ec, info)

                micRoom.startAcrossPK(acrossPK, pkRoomInfo)

    def refusedAcrossPK(self, roomId, userId, pkRoomId):
        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.refusedAcrossPK(userId, pkRoomId)

    def searchRoom(self, roomId, userId, searchId):
        searchRoom = MicServer.roomDao.searchRoom(searchId)
        if not searchRoom or not searchRoom.guildId:
            raise TTException(-1, "该房间不是派对房")
        searchRoomOwnerUser = MicServer.userDao.loadUser(searchRoom.ownerUserId)

        with self._roomLock.lock(roomId):
            micRoom = self._ensureActiveRoom(roomId)
            micRoom.searchRoom(userId, searchRoom, searchRoomOwnerUser)

    def pushMsgToRoom(self, roomId, msg):
        dmsg = strutil.jsonLoads(msg)
        if dmsg and isinstance(dmsg, dict) and dmsg.get('msgId') == 2030:
            with self._roomLock.lock(roomId):
                micRoom = self._ensureActiveRoom(roomId)
                if micRoom.roomTeamPK or micRoom.acrossRoomPK:
                    micRoom.pushRoomMsg(dmsg)

    def sendEmoticon(self, roomId, user, msg):
        emoticonId = strutil.jsonLoads(msg)
        emoticon = MicServer.confDao.loadEmoticon(user.userId, emoticonId)
        if emoticon is None:
            raise TTException(ErrorCode.BAD_PARAMS, '表情不存在')

        activeRoom = self.findActiveRoom(roomId)
        if activeRoom:
            micUser = activeRoom.findMicUser(user.userId)
            if not micUser:
                raise TTException(ErrorCode.OP_FAILED)
            activeRoom.sendEmoticon(micUser, emoticon)

    def updateRoomData(self, roomId, dataType):
        '''
        更新房间信息
        '''
        room = MicServer.roomDao.loadRoom(roomId)
        with self._roomLock.lock(roomId):
            micRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
            if micRoom:
                micRoom.updateRoomData(room, dataType)

    def banRoom(self, roomId, operator, reasonInfo):
        '''
        封禁房间
        '''
        with self._roomLock.lock(roomId):
            activeRoom = MicServer.activeRoomManager.findActiveRoom(roomId)
            if activeRoom:
                if activeRoom.acrossRoomPK:
                    raise TTException(ErrorCode.ACORSS_ROOM_EXISTS, '跨房pk中，不能封禁')

                activeRoom.banRoom(operator, reasonInfo)

            room_remote_proxy.banRoom(roomId, operator, reasonInfo)

    def disableRoomMsg(self, roomId, userId, disabled):
        '''
        关闭公屏
        '''
        roomStatus = MicServer.roomStatusDao.loadRoomStatus(roomId) or RoomStatus()
        roomStatus.disabledMsg = disabled
        MicServer.roomStatusDao.saveRoomStatus(roomId, roomStatus)
        fqparty.app.fire(RoomDisabledMsgEvent(roomId, roomStatus))

    def _checkPKOpen(self, userId, date):
        startHour = int(fqparty.app.utilService.getPKOpenConfByKey('start_hour') or -1)
        endHour = int(fqparty.app.utilService.getPKOpenConfByKey('end_hour') or -1)
        curHour = int(time.localtime().tm_hour)
        if curHour >= startHour and curHour <= endHour:
            num = int(fqparty.app.utilService.getPKOpenConfByKey('num') or 2)
            userNum = int(fqparty.app.utilService.getPKOpenNum(date, userId))
            ttlog.info("_checkPKOpen ", userId, startHour, endHour, curHour, num, userNum)
            if userNum >= num:
                openMsg = fqparty.app.utilService.getPKOpenConfByKey('msg')
                if not openMsg:
                    openMsg = '自然日%s:00-%s:00期间，单用户至多可开启%s次PK'
                raise TTException(-1, openMsg % (startHour, endHour, num))

            return True

        return False

