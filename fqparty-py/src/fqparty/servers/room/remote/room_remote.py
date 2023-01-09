# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty.decorator.decorator import remoteExceptionHandler
from fqparty.proxy.room import room_remote_proxy
from fqparty.servers.room import RoomServer
from tomato.decorator.decorator import remoteMethod


__serviceName__ = room_remote_proxy.REMOTE_SERVICE_NAME


@remoteMethod()
@remoteExceptionHandler
def userHeartbeat(roomId, userId):
    # TODO 用户心跳
    RoomServer.roomService.userHeartbeat(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def isUserInRoom(roomId, userId):
    return RoomServer.roomService.isUserInRoom(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def userEnterRoom(roomId, userId, password):
    RoomServer.roomService.userEnterRoom(roomId, userId, password)

@remoteMethod()
@remoteExceptionHandler
def userLeaveRoom(roomId, userId, reason, reasonInfo):
    RoomServer.roomService.userLeaveRoom(roomId, userId, reason, reasonInfo)

@remoteMethod()
@remoteExceptionHandler
def userOnMic(roomId, userId, micId):
    RoomServer.roomService.userOnMic(roomId, userId, micId)

@remoteMethod()
@remoteExceptionHandler
def userLeaveMic(roomId, userId, reason):
    RoomServer.roomService.userLeaveMic(roomId, userId, reason)

@remoteMethod()
@remoteExceptionHandler
def getRoomUserInfo(roomId, userId, queryUserId):
    RoomServer.roomService.getRoomUserInfo(roomId, userId, queryUserId)

@remoteMethod()
@remoteExceptionHandler
def getRoomUserListAll(roomId, userId,  pageIndex, pageNum):
    RoomServer.roomService.getRoomUserListAll(roomId, userId,  pageIndex, pageNum)

@remoteMethod()
@remoteExceptionHandler
def getRoomUserListThree(roomId, userId,  num):
    RoomServer.roomService.getRoomUserListThree(roomId, userId,  num)

@remoteMethod()
@remoteExceptionHandler
def disableRoomMsg(roomId, userId, disabled):
    RoomServer.roomService.disableRoomMsg(roomId, userId, disabled)

@remoteMethod()
@remoteExceptionHandler
def pushRoomInfo(roomId, userId):
    RoomServer.roomService.pushRoomInfo(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def getUserMic(roomId, userId):
    micId = RoomServer.roomService.getUserMic(roomId, userId)
    return micId

@remoteMethod()
@remoteExceptionHandler
def syncMusicData(roomId, userId, msg):
    RoomServer.roomService.syncMusicData(roomId, userId, msg)

@remoteMethod()
@remoteExceptionHandler
def disableUserMsg(roomId, userId, disabled):
    RoomServer.roomService.disableUserMsg(roomId, userId, disabled)

@remoteMethod()
@remoteExceptionHandler
def userOffline(roomId, userId):
    RoomServer.roomService.userOffline(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def sendMsgToRoom(roomId, userId, msgType, msg):
    RoomServer.roomService.sendMsgToRoom(roomId, userId, msgType, msg)

@remoteMethod()
@remoteExceptionHandler
def pushMsgToRoom(roomId, msg, msgType):
    RoomServer.roomService.pushMsgToRoom(roomId, msg, msgType)

@remoteMethod()
@remoteExceptionHandler
def pushMsgToAllRoom(msg, excludeRoomIds, excludeUserIds, msgType):
    RoomServer.roomService.pushMsgToAllRoom(msg, excludeRoomIds, excludeUserIds, msgType)

@remoteMethod()
@remoteExceptionHandler
def lockRoom(roomId, locked):
    RoomServer.roomService.lockRoom(roomId, locked)

@remoteMethod()
@remoteExceptionHandler
def updateUserInfo(roomId, userId):
    RoomServer.roomService.updateUserInfo(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def syncRoomData(roomId, dataType):
    RoomServer.roomService.updateRoomData(roomId, dataType)

@remoteMethod()
@remoteExceptionHandler
def sendRoomMsg(roomId, msg, excludeUserIds, canIgnore=False):
    RoomServer.roomService.sendRoomProtoMsg(roomId, msg, excludeUserIds, canIgnore)

@remoteMethod()
@remoteExceptionHandler
def sendRoomMsgToUser(roomId, userId, msg):
    RoomServer.roomService.sendRoomProtoMsgToUser(roomId, userId, msg)

@remoteMethod()
@remoteExceptionHandler
def banRoom(roomId, operator, reasonInfo):
    RoomServer.roomService.banRoom(roomId, operator, reasonInfo)
    
    
    
    