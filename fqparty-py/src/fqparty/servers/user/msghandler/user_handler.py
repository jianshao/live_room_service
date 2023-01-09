# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty.const import UserLeaveRoomReason, MsgRoutes
from fqparty.decorator.decorator import exceptionHandler
from fqparty.servers.user import UserServer
from tomato.common.proxy import session_remote_proxy
from tomato.decorator.decorator import messageHandler
from tomato.utils import strutil


@messageHandler(MsgRoutes.ROOM_USER_ENTER)
@exceptionHandler
def userEnterRoom(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    password = msg.body.get('password')
    UserServer.userService.enterRoom(sessionInfo.userId, roomId, password)
    return {'ec': 0, 'info': 'success'}


@messageHandler(MsgRoutes.ROOM_USER_LEAVE)
@exceptionHandler
def userLeaveRoom(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    UserServer.userService.leaveRoom(sessionInfo.userId, roomId, UserLeaveRoomReason.USER_ACTIVE)


@messageHandler(MsgRoutes.ROOM_USER_INFO_UPDATE)
@exceptionHandler
def updateUserInfo(msg, sessionInfo):
    UserServer.userService.updateUserInfo(sessionInfo.userId)


@messageHandler(MsgRoutes.USER_HEARTBEAT)
@exceptionHandler
def userHeartbeat(msg, sessionInfo):
    activeUser = UserServer.userService.userActiveHeartbeat(sessionInfo.userId, '1')
    if activeUser:
        # 给客户端回消息
        session_remote_proxy.pushRawData(strutil.jsonDumps({'msgId':75}), sessionInfo.frontId, sessionInfo.userId)



