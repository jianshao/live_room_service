# -*- coding:utf-8 -*-
'''
Created on 2020年10月30日

@author: zhaojiangang
'''
from fqparty.const import UserLeaveRoomReason
from fqparty.decorator.decorator import remoteExceptionHandler
from fqparty.proxy.user import user_remote_proxy
from fqparty.servers.user import UserServer
from tomato.decorator.decorator import remoteMethod


__serviceName__ = user_remote_proxy.REMOTE_SERVICE_NAME


@remoteMethod()
@remoteExceptionHandler
def login(userId, sessionInfo):
    '''
    用户登录
    '''
    activeUser = UserServer.userService.login(userId, sessionInfo)
    return {
        'userId': userId,
        'roomId': activeUser.location.roomId if activeUser.location else None,
        'password': activeUser.location.password if activeUser.location else None
    }


@remoteMethod()
@remoteExceptionHandler
def loginAndEnterRoom(userId, roomId, sessionInfo, password):
    '''
    用户登录
    '''
    UserServer.userService.login(userId, sessionInfo, roomId, password)


@remoteMethod()
@remoteExceptionHandler
def logout(userId, reason):
    '''
    用户登出
    '''
    UserServer.userService.logout(userId, reason)

@remoteMethod()
@remoteExceptionHandler
def userHeartbeat(userId, pkg):
    '''
    用户心跳
    '''
    UserServer.userService.userActiveHeartbeat(userId, pkg)


@remoteMethod()
@remoteExceptionHandler
def getUserRoomLocation(userId):
    '''
    用户的当前位置
    '''
    location = UserServer.userService.getUserRoomLocation(userId)
    if location:
        return {
            'roomId': location.roomId,
            'password': None
        }
    return None

@remoteMethod()
@remoteExceptionHandler
def updateUserInfo(userId):
    '''
    检查用户的麦
    '''
    UserServer.userService.updateUserInfo(userId)


@remoteMethod()
@remoteExceptionHandler
def getUserInfo(userId):
    '''
    检查用户的麦
    '''
    user = UserServer.userService.getUserInfo(userId)
    if user:
        return user.toDict()
    return None

@remoteMethod()
@remoteExceptionHandler
def globalUserNotify(userId, msg):
    '''
    php推送客户端
    '''
    pass

@remoteMethod()
@remoteExceptionHandler
def checkUserLogin(userId, msg):
    '''
    检测用户登录长链接
    '''
    UserServer.userService.checkUserLogin(userId, msg)

@remoteMethod()
@remoteExceptionHandler
def kickoutRoomUser(userId, roomId):
    UserServer.userService.leaveRoom(userId, roomId, UserLeaveRoomReason.KICKOUT, "您被踢出")

@remoteMethod()
@remoteExceptionHandler
def userEnterRoom(userId, roomId, password):
    UserServer.userService.enterRoom(userId, roomId, password)

@remoteMethod()
@remoteExceptionHandler
def userLeaveRoom(userId, roomId, reason):
    UserServer.userService.leaveRoom(userId, roomId, reason)



