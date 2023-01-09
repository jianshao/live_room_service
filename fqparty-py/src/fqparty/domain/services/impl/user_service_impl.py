# -*- coding:utf-8 -*-
'''
Created on 2020年10月30日

@author: zhaojiangang
'''
import fqparty
from fqparty.const import ErrorCode, UserLeaveRoomReason
from fqparty.domain.events.events import UserLoginEvent, UserLogoutEvent
from fqparty.domain.models.location import RoomLocation
from fqparty.domain.services.user_service import UserService
from fqparty.proxy.room import room_remote_proxy
from fqparty.servers.user import UserServer
import tomato
from tomato.common.proxy import session_remote_proxy
from tomato.const import ConnLostReason
from tomato.core.exceptions import TTException
from tomato.core.lock import TTKeyLock
from tomato.utils import ttlog


class UserServiceImpl(UserService):
    def __init__(self):
        # 用户锁
        self._userLock = TTKeyLock()
    
    def login(self, userId, sessionInfo, enterRoomId=None, password=None):
        '''
        用户登录
        '''
        user = UserServer.userDao.loadUser(userId)
        if not user:
            raise TTException(ErrorCode.OP_FAILED, '用户不存在')

        with self._userLock.lock(userId):
            # 保存session
            UserServer.sessionInfoDao.saveSessionInfo(userId, sessionInfo)
            # 缓存用户
            UserServer.userCacheDao.saveUser(user)

            ttlog.info('User login ok',
                       'userId=', userId,
                       'sessionInfo=', sessionInfo)

            fqparty.app.fire(UserLoginEvent(userId, user))

            location = UserServer.roomLocationDao.loadRoomLocation(userId)
            if location and enterRoomId:
                if location.roomId != enterRoomId:
                    self._leaveRoom(userId, location.roomId, UserLeaveRoomReason.CONN_LOST)

            if enterRoomId:
                self._enterRoom(userId, enterRoomId, password)

    def logout(self, userId, reason):
        '''
        用户登出
        '''
        with self._userLock.lock(userId):
            location = UserServer.roomLocationDao.loadRoomLocation(userId)
            if location:
                sessionInfo = UserServer.sessionInfoDao.loadSessionInfo(userId) or {}
                sessionInfo['offline'] = True
                UserServer.sessionInfoDao.saveSessionInfo(userId, sessionInfo)
                self._userOffline(userId, location.roomId, sessionInfo)
                
            ttlog.info('User logout ok',
                       'userId=', userId,
                       'reason=', reason)

            fqparty.app.fire(UserLogoutEvent(userId))

    def userHeartbeat(self, userId, pkg):
        '''
        用户心跳
        '''
        with self._userLock.lock(userId):
            self._userHeartbeat(userId, pkg)
            ttlog.info('User heartbeat',
                       'userId=', userId)
    
    def userActiveHeartbeat(self, userId, pkg):
        '''
        用户主动心跳
        '''
        with self._userLock.lock(userId):
            self._userHeartbeat(userId, pkg)

            ttlog.info('User activeHeartbeat',
                       'userId=', userId)
            return True
        
    def enterRoom(self, userId, roomId, password):
        '''
        用户进入房间
        '''
        with self._userLock.lock(userId):
            user = UserServer.userCacheDao.loadUser(userId)
            if not user:
                raise TTException(ErrorCode.OP_FAILED, '用户不存在')

            location = UserServer.roomLocationDao.loadRoomLocation(userId)
            
            if location and location.roomId != roomId:
                self._leaveRoom(userId, location.roomId, UserLeaveRoomReason.USER_ACTIVE)
            
            self._enterRoom(userId, roomId, password)
    
    def leaveRoom(self, userId, roomId, reason, reasonInfo=None):
        '''
        用户离开房间
        '''
        with self._userLock.lock(userId):
            location = UserServer.roomLocationDao.loadRoomLocation(userId)
            if location and location.roomId == roomId:
                self._leaveRoom(userId, roomId, reason, reasonInfo)
            else:
                # 离开房间，不删除location
                # room_remote_proxy.userLeaveRoom(roomId, userId, reason, reasonInfo)
                ttlog.info('User leaveRoom failed',
                           'userId=', userId,
                           'roomId=', roomId,
                           'reason=', reason,
                           'location=', location.roomId if location else None)
    
    def updateUserInfo(self, userId):
        user = UserServer.userDao.loadUser(userId)
        if not user:
            raise TTException(ErrorCode.OP_FAILED, '用户不存在')
        
        with self._userLock.lock(userId):
            UserServer.userCacheDao.saveUser(user)
            
            location = UserServer.roomLocationDao.loadRoomLocation(userId)
            if location:
                room_remote_proxy.updateUserInfo(location.roomId, userId, True)

            ttlog.info('UpdateUserInfo ok',
                       'userId=', userId)

    def checkUserLogin(self, userId, msg):
        '''
        检查用户token
        '''
        token = fqparty.app.utilService.getTokenByUserId(userId)
        sessionInfo = UserServer.sessionInfoDao.loadSessionInfo(userId) or {}
        sessionToken = sessionInfo.get('token')
        ttlog.info('UserServiceImpl.checkUserLogin',
                   'userId=', userId,
                   'msg=', msg,
                   'token=', token,
                   'sessionToken=', sessionToken)
        if token != sessionToken:
            frontendId = sessionInfo.get('frontendId')
            if frontendId:
                session_remote_proxy.kickSession(frontendId, userId, None, ConnLostReason.CONN_KICKOUT, True)

    def _userHeartbeat(self, userId, pkg):
        '''
        用户心跳
        '''
        location = UserServer.roomLocationDao.loadRoomLocation(userId)
        if location:
            room_remote_proxy.userHeartbeat(location.roomId, userId)
    
    def _enterRoom(self, userId, roomId, password):
        ec, info = room_remote_proxy.userEnterRoom(roomId, userId, password)
        if ec != 0:
            raise TTException(ec, info)

        location = RoomLocation(roomId, tomato.app.serverId)
        UserServer.roomLocationDao.saveRoomLocation(userId, location)

        ttlog.info('User enterRoom ok',
                   'userId=', userId,
                   'roomId=', roomId)
    
    def _leaveRoom(self, userId, roomId, reason, reasonInfo=None):
        room_remote_proxy.userLeaveRoom(roomId, userId, reason, reasonInfo)
        UserServer.roomLocationDao.removeRoomLocation(userId)
        ttlog.info('User leaveRoom ok',
                   'userId=', userId,
                   'roomId=', roomId,
                   'reason=', reason)
    
    def _userOffline(self, userId, roomId, sessionInfo):
        if not sessionInfo.get('onMicForLogout'):
            self._leaveRoom(userId, roomId, UserLeaveRoomReason.CONN_LOST)
        else:
            room_remote_proxy.userOffline(roomId, userId)

        ttlog.info('User offline ok',
                   'userId=', userId,
                   'roomId=', roomId)

    def getUserRoomLocation(self, userId):
        '''获取用户当前位置'''
        location = UserServer.roomLocationDao.loadRoomLocation(userId)
        if location:
            ec, res = room_remote_proxy.isUserInRoom(location.roomId, userId)
            if res:
                return location

        return None


