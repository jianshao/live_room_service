# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
import math
from fqparty.decorator.decorator import exceptionHandler, exceptionRoomHandlerOld
from tomato.decorator.decorator import messageHandler
from fqparty.servers.room import RoomServer
from fqparty.const import MsgRoutes, UserLeaveMicReason


@messageHandler(MsgRoutes.ROOM_DISABLE_MSG)
@exceptionHandler
def userDisableRoomMsg(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    disabled = msg.body.get('disabled')

    RoomServer.roomService.disableRoomMsg(roomId, sessionInfo.userId, disabled)

@messageHandler(MsgRoutes.ROOM_USER_INFO)
@exceptionHandler
def getRoomUserInfo(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    queryUserId = msg.body.get('queryUserId')
    RoomServer.roomService.getRoomUserInfo(roomId, sessionInfo.userId, queryUserId)

@messageHandler(MsgRoutes.ROOM_USER_LIST)
@exceptionHandler
def getRoomUserList(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    pageIndex = msg.body.get('pageIndex', 0)
    pageNum = msg.body.get('pageNum', 20)
    RoomServer.roomService.getRoomUserListAll(roomId, sessionInfo.userId, pageIndex, pageNum)

@messageHandler(MsgRoutes.ROOM_USER_LIST_THREE)
@exceptionHandler
def getRoomUserListThree(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    num = msg.body.get('num', 3)
    RoomServer.roomService.getRoomUserListThree(roomId, sessionInfo.userId, num)

@messageHandler(MsgRoutes.ROOM_SEND_MSG_TO_ROOM)
@exceptionHandler
def sendMsgToRoom(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    msgType = msg.body.get('msgType')
    msg = msg.body.get('msg')
    RoomServer.roomService.sendMsgToRoom(roomId, sessionInfo.userId, msgType, msg)

@messageHandler(MsgRoutes.ROOM_ROOM_INFO)
@exceptionHandler
def pushRoomInfo(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    RoomServer.roomService.pushRoomInfo(roomId, sessionInfo.userId)

@messageHandler(MsgRoutes.ROOM_MIC_GET)
@exceptionHandler
def getUserMic(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    RoomServer.roomService.getUserMic(roomId, sessionInfo.userId)

@messageHandler(MsgRoutes.ROOM_SYNC_MUSIC)
@exceptionHandler
def syncMusicData(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    msg = msg.body.get('msg')
    RoomServer.roomService.syncMusicData(roomId, sessionInfo.userId, msg)

@messageHandler(MsgRoutes.ROOM_DISABLE_USER_MSG)
@exceptionHandler
def disableUserMsg(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    disabled = msg.body.get('disabled')
    RoomServer.roomService.disableUserMsg(roomId, sessionInfo.userId, disabled)

# @messageHandler(MsgRoutes.ROOM_KICKOUT_USER)
# @exceptionHandler
# def kickoutUser(msg, sessionInfo):
#     roomId = msg.body.get('roomId')
#     userId = msg.body.get('userId')
#     RoomServer.roomService.kickoutUser(roomId, userId)

@messageHandler('/user/joinPKLocation')
@exceptionRoomHandlerOld
def joinPKLocation(msg, sessionInfo):
    '''
    加入团队pk
    '''
    roomId = msg.body.get('roomId')
    teamLocation = msg.body.get('location')
    return RoomServer.roomService.joinPKLocation(roomId, sessionInfo.userId, teamLocation)


@messageHandler('/user/leavePKLocation')
@exceptionRoomHandlerOld
def leavePKLocation(msg, sessionInfo):
    '''
    下pk
    '''
    roomId = msg.body.get('roomId')
    return RoomServer.roomService.leavePKLocation(roomId, sessionInfo.userId, UserLeaveMicReason.USER_ACTIVE)

