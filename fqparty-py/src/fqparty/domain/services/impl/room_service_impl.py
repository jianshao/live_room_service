# -*- coding:utf-8 -*-
'''
Created on 2022年1月24日

@author: zhaojiangang
'''
import fqparty
from fqparty.const import ErrorCode, AdminTypes, UserLeaveRoomReason, MsgTypes
from fqparty.domain.events.events import UserEnterRoomEvent, UserReconnectRoomEvent, UserLeaveRoomEvent, SendTextMsgToRoomEvent, \
    DisabledUserMsgEvent, PushRoomInfoEvent, PushRoomUserListThreeEvent, PushRoomUserListAllEvent, RoomUserUpdateEvent, \
    PushRoomUserListEvent, LockRoomEvent, PushRoomUserInfoEvent, PushRoomLedMsgEvent, PushRoomMsgEvent, SendRoomMsgEvent, \
    SendRoomMsgToUserEvent, SendEmoticonEvent, UserHeartbeatEvent
from fqparty.domain.models.room import RoomUserStatus
from fqparty.domain.room.room import RoomUser
from fqparty.domain.services.room_service import RoomService
from fqparty.proxy.mic import mic_remote_proxy
from fqparty.proxy.user import user_remote_proxy
from fqparty.servers.room import RoomServer
import tomato
from tomato.config import configure
from tomato.core.exceptions import TTException
from tomato.core.lock import TTKeyLock
from tomato.core.timer import TTTaskletTimer
from tomato.utils import timeutil, ttlog, strutil, ttbilog


class RoomServiceImpl(RoomService):
    def __init__(self):
        # 用户锁
        self._userLock = TTKeyLock()
        # 离线用户检查
        self._offlineCheckTimer = TTTaskletTimer.runForever(10, self._checkOfflineUsers)
        self._activeRoomCheckTimer = TTTaskletTimer.runForever(10, self._checkActiveRoom)
        self._updateRoomTop3Timer = TTTaskletTimer.runForever(6, self._updateAllRoomTop3)
        
    def isUserInRoom(self, roomId, userId):
        '''
        检查用户是否在房间
        '''
        roomUser = self.findRoomUser(userId)
        return roomUser and roomUser.roomId == roomId

    def findRoomUser(self, userId):
        return RoomServer.roomUserManager.findRoomUser(userId)

    def getAllUserCount(self):
        return RoomServer.roomUserManager.getAllUserCount()
    
    def getRoomUserCount(self, roomId):
        return RoomServer.roomUserManager.getUserCountByRoom(roomId)
    
    def banRoom(self, roomId, operator, reasonInfo):
        '''
        封禁房间
        '''
        roomUsers = RoomServer.roomUserManager.getRoomUsersByRoomId(roomId)
        if roomUsers:
            activeRoom = RoomServer.activeRoomManager.findActiveRoom(roomId)

            fqparty.app.fire(UserLeaveRoomEvent(activeRoom, None, UserLeaveRoomReason.BAN_ROOM, reasonInfo))

    def userEnterRoom(self, roomId, userId, password):
        '''
        用户进入房间
        '''
        with self._userLock.lock(userId):
            user = RoomServer.userCacheDao.loadUser(userId)
            if not user:
                raise TTException(ErrorCode.USER_NOT_LOGIN)
            
            # 用户房间状态
            roomUser = self.findRoomUser(userId)
            
            if not roomUser:
                self._checkCanEnterRoom(roomId, user)
            else:
                roomUser.user = user
            
            # 加载活跃房间
            activeRoom, _ = RoomServer.activeRoomManager.findOrLoadActiveRoom(roomId, user)
            
            if roomUser and roomUser.roomId != roomId:
                # 先离开其它房间
                self._leaveRoom(activeRoom, roomUser, UserLeaveRoomReason.USER_ACTIVE)
                roomUser = None
           
            sessionInfo = RoomServer.sessionInfoDao.loadSessionInfo(userId) or {}
            
            if not roomUser:
                # 进入房间
                roomUser = self._enterRoom(activeRoom, user, sessionInfo, password)
            else:
                self._reconnectRoom(activeRoom, roomUser, sessionInfo)
            
            return roomUser

    def userLeaveRoom(self, roomId, userId, reason, reasonInfo):
        '''
        离开房间
        '''
        with self._userLock.lock(userId):
            roomUser = self.findRoomUser(userId)
            if roomUser:
                # 加载活跃房间
                activeRoom, _ = RoomServer.activeRoomManager.findOrLoadActiveRoom(roomId, roomUser.user)
                # 离开房间
                self._leaveRoom(activeRoom, roomUser, reason, reasonInfo)
            else:
                ttlog.warn('LeaveRoom failed',
                           'roomId=', roomId,
                           'userId=', userId,
                           'reason=', reason,
                           'err=', 'UserNotInRoom')
    
    def userOffline(self, roomId, userId):
        '''
        用户断线
        '''
        with self._userLock.lock(userId):
            roomUser = self.findRoomUser(userId)
            if roomUser and roomUser.roomId == roomId:
                roomUser.sessionInfo = RoomServer.sessionInfoDao.loadSessionInfo(userId) or {}

                ttlog.info('User offline',
                           'roomId=', roomId,
                           'userId=', userId,
                           'realRoomId=', roomUser.roomId,
                           'sessionInfo=', roomUser.sessionInfo)

    def userHeartbeat(self, roomId, userId):
        '''
        用户心跳
        '''
        curTime = timeutil.currentTimestamp()
        with self._userLock.lock(userId):
            roomUser = self.findRoomUser(userId)
            if roomUser and roomUser.roomId == roomId:
                duration = curTime - roomUser.lastHeartbeatTime
                if duration >= 60:
                    fqparty.app.fire(UserHeartbeatEvent(roomUser, duration))
                    roomUser.lastHeartbeatTime = curTime

                roomUser.status.heartbeatTime = curTime
                RoomServer.roomUserStatusDao.saveRoomUserStatus(roomId, userId, roomUser.status)
                mic_remote_proxy.userHeartbeat(roomId, userId)
                if ttlog.isDebugEnabled():
                    ttlog.debug('UserHeartbeat ok',
                                'roomId=', roomId,
                                'userId=', roomUser.userId)
                    
    def userOnMic(self, roomId, userId, micId):
        with self._userLock.lock(userId):
            roomUser = self._ensureRoomUser(roomId, userId)
            ec, info = mic_remote_proxy.userOnMic(roomId, roomUser.user.toDict(), micId)
            if ec != 0:
                raise TTException(ec, info)

    def pushRoomInfo(self, roomId, userId):
        '''
        给用户发送房间信息
        '''
        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        
        ttlog.info('PushRoomInfo ok',
                   'roomId=', roomId,
                   'userId=', roomUser.userId)
        
        fqparty.app.fire(PushRoomInfoEvent(activeRoom, roomUser))
        
    def userLeaveMic(self, roomId, userId, reason):
        with self._userLock.lock(userId):
            self._ensureRoomUser(roomId, userId)
            
            ec, info = mic_remote_proxy.userLeaveMic(roomId, userId, reason)
            if ec != 0:
                raise TTException(ec, info)

    def sendMsgToRoom(self, roomId, userId, msgType, msg):
        if fqparty.app.utilService.isReportDisabledMsgUser(userId):
            raise TTException(-1, '您因违规已被禁言')

        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        if roomUser.status.disabledMsg:
            raise TTException(-1, '您被禁言')

        ttlog.info('sendMsgToRoom ok',
                   'roomId=', roomId,
                   'userId=', userId,
                   'msgType=', msgType,
                   'msg=', msg)

        if msgType == MsgTypes.TEXT:
            roomUser.chatInfo.incrChatCount(timeutil.currentTimestamp())
            fqparty.app.fire(SendTextMsgToRoomEvent(activeRoom, roomUser, msgType, msg))

            self._recordChatMsg(roomId, userId, msg)
        elif msgType == MsgTypes.MIC_EMIOC:
            ec, info = mic_remote_proxy.sendEmoticon(roomId, roomUser.user.toDict(), msg)
            if ec == 0:
                roomUser.chatInfo.incrChatCount(timeutil.currentTimestamp())
                fqparty.app.fire(SendEmoticonEvent(activeRoom, roomUser, msg))
            else:
                raise TTException(ec, info)

    def _recordChatMsg(self, roomId, userId, msg):
        newmsg = strutil.jsonLoads(msg)
        contentType = newmsg.get('messageType')
        if contentType == 0:
            from sre_compile import isstring
            text = newmsg.get('content', {}).get('text')
            if isstring(text):
                ttbilog.info(strutil.jsonDumps({
                    'type': 'user_room_chat',
                    'userId': userId,
                    'roomId': roomId,
                    'content': text,
                    'createTime': timeutil.currentTimestamp()
                }))

    def disableUserMsg(self, roomId, userId, disabled):
        '''
        用户禁言
        '''
        with self._userLock.lock(userId):
            activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
            if not roomUser.status.disabledMsg ^ disabled:
                return
            
            roomUser.status.disabledMsg = disabled
            RoomServer.roomUserStatusDao.saveRoomUserStatus(roomId, userId, roomUser.status)
            
            ttlog.info('DisableUserMsg ok',
                       'roomId=', roomId,
                       'user=', roomUser.userId,
                       'disabled=', roomUser.status.disabledMsg)

            fqparty.app.fire(DisabledUserMsgEvent(activeRoom, roomUser, disabled))

    def getUserMic(self, roomId, userId):
        '''
        获取用户麦位
        '''
        with self._userLock.lock(userId):
            micId = 0
            roomUser = self._ensureRoomUser(roomId, userId)
            if roomUser:
                micUserStatus = RoomServer.micUserStatusDao.loadMicUserStatus(roomId, userId)
                micId = micUserStatus.micId if micUserStatus else 0
            return micId
    
    def getRoomUserList(self, roomId, userId, listType):
        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)

        ttlog.info('getRoomUserList ok',
                   'roomId=', roomId,
                   'userId=', userId,
                   'listType=', listType)

        fqparty.app.fire(PushRoomUserListEvent(activeRoom, roomUser, listType))

    def getRoomUserListAll(self, roomId, userId, pageIndex, pageNum):
        pageNum = 20 if pageNum > 100 or pageNum < 0 else pageNum
        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        
        ttlog.info('getRoomUserListAll ok',
                   'roomId=', roomId,
                   'userId=', userId,
                   'pageIndex=', pageIndex,
                   'pageNum=', pageNum)

        fqparty.app.fire(PushRoomUserListAllEvent(activeRoom, roomUser, pageIndex, pageNum))
    
    def getRoomUserListThree(self, roomId, userId, num):
        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        
        ttlog.info('GetRoomUserListThree ok',
                   'roomId=', roomId,
                   'user=', roomUser.userId)
        
        fqparty.app.fire(PushRoomUserListThreeEvent(activeRoom, roomUser))

    def syncMusicData(self, roomId, userId, msg):
        '''
        同步音乐数据
        '''
        pass
    
    def updateUserInfo(self, roomId, userId):
        '''
        更新用户信息
        '''
        with self._userLock.lock(userId):
            activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
            user = RoomServer.userCacheDao.loadUser(userId)
            if user:
                roomUser.user = user
                roomUser.dayConsume = RoomServer.getDayConsume(roomId, userId)
                # 更新
                score = self.calcRoomUserScore(roomUser)
                RoomServer.roomOnlineUserListDao.setRoomOnlineUser(roomId, userId, score)
                ttlog.info('UpdateUserInfo ok',
                           'roomId=', roomId,
                           'userId=', user.userId)
    
                fqparty.app.fire(RoomUserUpdateEvent(activeRoom, roomUser))

                if userId in activeRoom.top3UserIds:
                    fqparty.app.fire(PushRoomUserListThreeEvent(activeRoom))

    def updateRoomData(self, roomId, dataType):
        activeRoom = self._ensureActiveRoom(roomId)
        if activeRoom:
            room = RoomServer.roomDao.loadRoom(roomId)
            activeRoom.room = room

    def getRoomUserInfo(self, roomId, userId, queryUserId):
        activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        queryRoomUser = self.findRoomUser(queryUserId)

        attention = RoomServer.attentionDao.loadAttention(userId, queryUserId)
        isAttention = True if attention else False
        if queryRoomUser and queryRoomUser.roomId == roomId:
            fqparty.app.fire(PushRoomUserInfoEvent(activeRoom, roomUser, queryRoomUser, isAttention, True))
        elif RoomServer.roomOnlineUserListDao.existsRoomOnlineUser(roomId, queryUserId):
            sessionInfo = RoomServer.sessionInfoDao.loadSessionInfo(queryUserId) or {}
            roomUserStatus = RoomServer.roomUserStatusDao.loadRoomUserStatus(roomId, queryUserId) or RoomUserStatus()
            user = RoomServer.userCacheDao.loadUser(queryUserId)
            fqparty.app.fire(
                PushRoomUserInfoEvent(activeRoom, roomUser, RoomUser(activeRoom, user, roomUserStatus, sessionInfo), isAttention, True))
        else:
            user = RoomServer.userDao.loadUser(queryUserId)
            if user:
                fqparty.app.fire(PushRoomUserInfoEvent(activeRoom, roomUser, RoomUser(activeRoom, user, RoomUserStatus(), {}), isAttention, False))

    def lockRoom(self, roomId, locked):
        ttlog.info('LockRoom ok',
                   'roomId=', roomId)
        activeRoom = self._ensureActiveRoom(roomId)
        activeRoom.room.roomLock = locked
        fqparty.app.fire(LockRoomEvent(activeRoom, locked))

    def disableRoomMsg(self, roomId, userId, disabled):
        '''
        开启/关闭公屏
        @param roomId: 要开启/关闭的房间
        @param userId: 哪个用户开启/关闭
        @param disabled: True: 开 False: 关
        '''
        _activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
        
        mic_remote_proxy.disableRoomMsg(roomId, userId, disabled)
        
        ttlog.info('DisableRoomMsg ok',
                   'roomId=', roomId,
                   'user=', roomUser.userId,
                   'disabled=', disabled)
        
    def joinPKLocation(self, roomId, userId, location):
        '''
        加入pk位置
        '''
        with self._userLock.lock(userId):
            _activeRoom, roomUser = self._ensureActiveRoomAndRoomUser(roomId, userId)
            ec, info = mic_remote_proxy.joinPKLocation(roomId, roomUser.user.toDict(), location)
            if ec != 0:
                raise TTException(ec, info)
            ttlog.info('JoinPkLocation ok',
                       'roomId=', roomId,
                       'userId=', userId,
                       'location=', location)
    
    def leavePKLocation(self, roomId, userId, reason):
        '''
        离开pk
        '''
        with self._userLock.lock(userId):
            self._ensureActiveRoomAndRoomUser(roomId, userId)
            ec, info = mic_remote_proxy.leavePKLocation(roomId, userId, reason)
            if ec != 0:
                raise TTException(ec, info)
            ttlog.info('LeavePkLocation ok',
                       'roomId=', roomId,
                       'userId=', userId,
                       'reason=', reason)
    
    def calcRoomUserScore(self, roomUser):
        #本房间当日消费>爵位＞等级＞会员＞靓号＞麦位号
        dayConsumeScore = 100000 * roomUser.dayConsume
        dukeScore = 10000 * roomUser.user.dukeId
        levelScore = 1000 * roomUser.user.userLevel
        vipScore = 100 * roomUser.user.isVip
        prettyScore = 10 * 0 if roomUser.user.userId != roomUser.user.prettyId else 1
        micScore = 0 # roomUser.micId TODO
        return dayConsumeScore + dukeScore + levelScore + vipScore + prettyScore + micScore

    def _checkCanEnterRoom(self, roomId, user):
        '''
        检查是否可以进房间
        '''
        if user.dukeId < 5 and fqparty.app.utilService.isKickoutUser(roomId, user.userId):
            raise TTException(ErrorCode.ENTER_ROOM_FORBBIDEN, '您已被加入黑名单')
    
        if fqparty.app.utilService.isSystemKickoutUser(roomId, user.userId):
            raise TTException(ErrorCode.ENTER_ROOM_FORBBIDEN, '您已被平台管理员踢出当前房间')
    
        if fqparty.app.utilService.isBannedRoom(roomId):
            raise TTException(ErrorCode.ENTER_ROOM_FORBBIDEN, '该房间违规封禁中')

        maxRoomCount = RoomServer.confDao.getMaxRoomCount()
        if RoomServer.roomUserManager.getUserCountByRoom(roomId) > maxRoomCount:
            raise TTException(ErrorCode.OP_FAILED, '房间太火爆，请稍后再试')

    def _ensureActiveRoom(self, roomId):
        activeRoom, _ = RoomServer.activeRoomManager.findOrLoadActiveRoom(roomId, None)
        if not activeRoom:
            raise TTException(ErrorCode.ROOM_NOT_EXISTS)
        return activeRoom
    
    def _ensureRoomUser(self, roomId, userId):
        roomUser = self.findRoomUser(userId)
        if roomUser and roomUser.roomId == roomId:
            return roomUser
        raise TTException(ErrorCode.USER_NOT_IN_ROOM)
    
    def _ensureActiveRoomAndRoomUser(self, roomId, userId):
        roomUser = self._ensureRoomUser(roomId, userId)
        activeRoom = self._ensureActiveRoom(roomId)
        return activeRoom, roomUser
    
    def _addRoomUser(self, activeRoom, roomUser):
        RoomServer.roomUserManager.addRoomUser(roomUser)
        # 保存到redis
        RoomServer.roomUserStatusDao.saveRoomUserStatus(activeRoom.roomId, roomUser.userId, roomUser.status)
        # 保存到房间用户列表
        score = self.calcRoomUserScore(roomUser)
        RoomServer.roomOnlineUserListDao.setRoomOnlineUser(activeRoom.roomId, roomUser.userId, score)
        # 保存到当前进程在线列表
        RoomServer.roomServerOnlineUserDao.addRoomOnlineUser(tomato.app.serverId, roomUser.userId, activeRoom.roomId)
                
    def _removeRoomUser(self, roomUser):
        RoomServer.roomUserManager.removeRoomUser(roomUser)
        # 从房间用户列表删除
        RoomServer.roomOnlineUserListDao.removeRoomOnlineUser(roomUser.roomId, roomUser.userId)
        # 从当前进程在线列表删除
        RoomServer.roomServerOnlineUserDao.removeRoomOnlineUser(tomato.app.serverId, roomUser.userId)
        # 从redis删除
        RoomServer.roomUserStatusDao.removeRoomUserStatus(roomUser.roomId, roomUser.userId)

    def _enterRoom(self, activeRoom, user, sessionInfo, password):
        '''
        用户进入房间
        '''
        # 未实名的个人工会放不可以进房间
        if not activeRoom.room.guildId and activeRoom.ownerUserId == user.userId and user.attestation != 1:
            if configure.loadJson('server.fqparty.global', {}).get('mode') != 'test':
                raise TTException(ErrorCode.ENTER_ROOM_FORBBIDEN, '根据《网络游戏管理暂行办法》的要求，用户在未实名的情况下，部分功能使用受限')

        # 密码检查
        self._checkPassword(activeRoom, user, password)
        # 生成房间用户
        roomUserStatus = RoomUserStatus()
        roomUserStatus.enterTime = timeutil.currentTimestamp()
        roomUserStatus.heartbeatTime = roomUserStatus.enterTime
        roomUserStatus.disabledMsg = fqparty.app.utilService.isDisabledMsgUser(activeRoom.roomId, user.userId)
        dayConsume = RoomServer.getDayConsume(activeRoom.roomId, user.userId)
        roomUser = RoomUser(activeRoom.roomId, user, roomUserStatus, sessionInfo, dayConsume)
        # 保存
        self._addRoomUser(activeRoom, roomUser)
        
        ttlog.info('EnterRoom ok',
                   'roomId=', roomUser.roomId,
                   'userId=', roomUser.userId,
                   'roomUserCount=', self.getRoomUserCount(roomUser.roomId),
                   'allUserCount=', self.getAllUserCount())

        ttbilog.info(strutil.jsonDumps({
            'type': 'user_enter_room',
            'userId': roomUser.userId,
            'roomId': roomUser.roomId,
            'logTime': roomUserStatus.enterTime
        }))

        fqparty.app.fire(UserEnterRoomEvent(activeRoom, roomUser))
        
        return roomUser
    
    def _reconnectRoom(self, activeRoom, roomUser, sessionInfo):
        '''
        用户重新进入房间
        '''
        roomUser.sessionInfo = sessionInfo
        
        ttlog.info('ReconnectRoom ok',
                   'roomId=', activeRoom.roomId,
                   'userId=', roomUser.userId,
                   'sessionInfo=', roomUser.sessionInfo)

        fqparty.app.fire(UserReconnectRoomEvent(activeRoom, roomUser))
    
    def _leaveRoom(self, activeRoom, roomUser, reason, reasonInfo=None):
        '''
        离开房间
        '''
        # 从内存删除
        self._removeRoomUser(roomUser)
        
        micUserStatus = RoomServer.micUserStatusDao.loadMicUserStatus(activeRoom.roomId, roomUser.userId)
        
        if micUserStatus:
            if micUserStatus.micId:
                mic_remote_proxy.onUserLeaveRoom(activeRoom.roomId, roomUser.userId, reason)

            if micUserStatus.userId in activeRoom.top3UserIds:
                top3UserIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(activeRoom.roomId, 0, 3)
                activeRoom.top3UserIds = top3UserIds
                fqparty.app.fire(PushRoomUserListThreeEvent(activeRoom))

        ttlog.info('LeaveRoom ok',
                   'roomId=', roomUser.roomId,
                   'userId=', roomUser.userId,
                   'reason=', reason,
                   'roomUserCount=', self.getRoomUserCount(roomUser.roomId),
                   'allUserCount=', self.getAllUserCount())

        curTime = timeutil.currentTimestamp()
        ttbilog.info(strutil.jsonDumps({
            'type': 'user_leave_room',
            'userId': roomUser.userId,
            'roomId': roomUser.roomId,
            'duration': curTime - roomUser.status.enterTime,
            'logTime': roomUser.status.enterTime,
            'leaveTime': curTime,
            'reason': reason,
        }))
        
        # 触发事件
        fqparty.app.fire(UserLeaveRoomEvent(activeRoom, roomUser, reason, reasonInfo))

    def _checkPassword(self, activeRoom, user, password):
        roomLockPassword = fqparty.app.utilService.getRoomLockPassword(activeRoom.roomId)
        if roomLockPassword:
            roomAdmin = activeRoom.findAdmin(user.userId)
            if (activeRoom.ownerUserId != user.userId
                    and user.role != AdminTypes.OFFICAL
                    and (not roomAdmin or roomAdmin.adminType not in (AdminTypes.OWNER, AdminTypes.ADMIN, AdminTypes.OFFICAL))):
                # 没有输入密码提示输入密码
                if password is None:
                    raise TTException(ErrorCode.ENTER_ROOM_LOCK, '房间被锁了')

                # 不是房主和官方和管理员需要检查密码
                if password != roomLockPassword:
                    raise TTException(ErrorCode.ENTER_ROOM_ERR_PASSWORD, '密码错误')
    
    def _checkOffline(self, userId, offlineTimeout):
        curTime = timeutil.currentTimestamp()
        with self._userLock.lock(userId):
            roomUser = self.findRoomUser(userId)
            if roomUser and curTime >= roomUser.status.heartbeatTime + offlineTimeout:
                user_remote_proxy.userLeaveRoom(userId, roomUser.roomId, UserLeaveRoomReason.CONN_TIMEOUT, True)

    def _checkOfflineUsers(self):
        offlineUserIds = []
        curTime = timeutil.currentTimestamp()
        timeouts = configure.loadJson('server.fqparty.global', {}).get('timeouts', {})
        offlineTimeout = timeouts.get('offlineTimeout', 30)
        roomUserMap = RoomServer.roomUserManager.getRoomUsersMap()
        for _, roomUser in roomUserMap.iteritems():
            if curTime >= roomUser.status.heartbeatTime + offlineTimeout:
                offlineUserIds.append(roomUser.userId)
        
        for userId in offlineUserIds:
            self._checkOffline(userId, offlineTimeout)
        
        if ttlog.isDebugEnabled():
            ttlog.debug('CheckOfflineUsers',
                        'serverId=', tomato.app.serverId,
                        'userIds=', offlineUserIds)
    
    def _checkActiveRoom(self):
        '''
        N秒检查一次，踢出没有pk的没人的房间
        '''
        activeRoomMap = RoomServer.activeRoomManager.getActiveRoomMap()
        roomIds = set(activeRoomMap.keys())

        if ttlog.isDebugEnabled():
            ttlog.debug('CheckActiveRoom',
                        'serverId=', tomato.app.serverId,
                        'roomIds=', roomIds)

        for roomId in roomIds:
            if RoomServer.roomUserManager.getUserCountByRoom(roomId) == 0:
                RoomServer.activeRoomManager.removeActiveRoom(roomId)
                ttlog.info('CheckActiveRoom remove',
                           'serverId=', tomato.app.serverId,
                           'roomId=', roomId)
    
    def _updateRoomTop3(self, activeRoom):
        top3UserIds = RoomServer.roomOnlineUserListDao.getRoomOnlineUserIds(activeRoom.roomId, 0, 3)
        if top3UserIds != activeRoom.top3UserIds:
            activeRoom.top3UserIds = top3UserIds
            fqparty.app.fire(PushRoomUserListThreeEvent(activeRoom))
    
    def _updateAllRoomTop3(self):
        activeRoomMap = RoomServer.activeRoomManager.getActiveRoomMap()
        activeRooms = list(activeRoomMap.values())
        for activeRoom in activeRooms:
            self._updateRoomTop3(activeRoom)

    def _pushRoomMsg(self, activeRoom, msg, isBroadcast, excludeUserIds=[], type=None):
        from fqparty.utils import proto_utils
        canIgnore = False
        canntIgnoreUserIds = set()
        try:
            dmsg = strutil.jsonLoads(msg)
            if dmsg and isinstance(dmsg, dict) and dmsg.get('msgId') in (2031, 2030):
                if 'VisitorNum' in dmsg:
                    heartValue = fqparty.app.utilService.getRoomHeatScore(activeRoom.roomId)
                    dmsg['VisitorNum'] = proto_utils.buildRoomHeatValue(heartValue)
                    msg = strutil.jsonDumps(dmsg)
                if dmsg.get('msgId') == 2030:
                    # 送礼
                    canIgnore = True
                    senderUserId = dmsg.get('GiftGiver', {}).get('UserId', 0)
                    if senderUserId != 0:
                        canntIgnoreUserIds.add(int(senderUserId))
                    for receiveData in dmsg.get('GiveGiftDatas', []):
                        receiveId = receiveData.get('userId', 0)
                        if receiveId != 0:
                            canntIgnoreUserIds.add(receiveId)
        except Exception, e:
            ttlog.warn('PushRoomMsg',
                       'roomId=', activeRoom.roomId,
                       'isBroadcast=', False,
                       'msg=', msg,
                       'ex=', e)
        if type == 'led':
            fqparty.app.fire(PushRoomLedMsgEvent(activeRoom, msg, excludeUserIds))
        else:
            fqparty.app.fire(PushRoomMsgEvent(activeRoom, msg, isBroadcast, excludeUserIds, canIgnore, canntIgnoreUserIds))

    def pushMsgToRoom(self, roomId, msg, msgType):
        activeRoom = RoomServer.activeRoomManager.findActiveRoom(roomId)
        if activeRoom:
            self._pushRoomMsg(activeRoom, msg, False, type=msgType)

    def pushMsgToAllRoom(self, msg, excludeRoomIds, excludeUserIds, msgType):
        activeRoomMap = RoomServer.activeRoomManager.getActiveRoomMap()
        for activeRoom in activeRoomMap.values():
            if not excludeRoomIds or (activeRoom.roomId not in excludeRoomIds):
                self._pushRoomMsg(activeRoom, msg, True, excludeUserIds, type=msgType)

    def sendRoomProtoMsg(self, roomId, msg, excludeUserIds, canIgnore=False):
        activeRoom = RoomServer.activeRoomManager.findActiveRoom(roomId)
        if activeRoom:
            fqparty.app.fire(SendRoomMsgEvent(activeRoom, msg, excludeUserIds, canIgnore))

    def sendRoomProtoMsgToUser(self, roomId, userId, msg):
        activeRoom = RoomServer.activeRoomManager.findActiveRoom(roomId)
        if activeRoom:
            roomUser = self.findRoomUser(userId)
            if roomUser and roomUser.roomId == roomId:
                fqparty.app.fire(SendRoomMsgToUserEvent(activeRoom, roomUser, msg))



