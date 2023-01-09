# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
import math
from fqparty.decorator.decorator import exceptionHandler, exceptionRoomHandlerOld
from tomato.decorator.decorator import messageHandler
from fqparty.servers.mic import MicServer
from fqparty.const import MsgRoutes, UserLeaveMicReason

@messageHandler(MsgRoutes.ROOM_PK_START)
@exceptionRoomHandlerOld
def startPK(msg, sessionInfo):
    '''
    开始pk
    '''
    roomId = msg.body.get('roomId')
    redList = msg.body.get('redList', [])
    blueList = msg.body.get('blueList', [])
    punishment = msg.body.get('punishment', '')
    countdown = msg.body.get('countdown')
    return MicServer.micRoomService.startPK(roomId, sessionInfo.userId, redList, blueList, punishment, countdown)

@messageHandler(MsgRoutes.ROOM_PK_END)
@exceptionRoomHandlerOld
def endPK(msg, sessionInfo):
    '''
    结束pk
    '''
    roomId = msg.body.get('roomId')
    return MicServer.micRoomService.endPK(roomId, sessionInfo.userId)


@messageHandler(MsgRoutes.ROOM_PK_ADD_COUNTDOWN)
@exceptionRoomHandlerOld
def addPKCountdown(msg, sessionInfo):
    '''
    结束pk
    '''
    roomId = msg.body.get('roomId')
    duration = msg.body.get('duration')
    return MicServer.micRoomService.addPKCountdown(roomId, sessionInfo.userId, duration)


@messageHandler(MsgRoutes.ROOM_CREATE_ACORSS_PK)
@exceptionRoomHandlerOld
def createAcrossPK(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    punishment = msg.body.get('punishment', '')
    countdown = msg.body.get('countdown')
    cancel = msg.body.get('cancel')
    if cancel:
        MicServer.micRoomService.cancelCreateAcrossPK(roomId, sessionInfo.userId)
    else:
        MicServer.micRoomService.createAcrossPK(roomId, sessionInfo.userId, punishment, countdown)


@messageHandler(MsgRoutes.ROOM_ACORSS_PK_LIST)
@exceptionRoomHandlerOld
def createAcorssPKList(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    MicServer.micRoomService.createAcorssPKList(roomId, sessionInfo.userId)


@messageHandler(MsgRoutes.ROOM_SPONSORE_ACORSS_PK)
@exceptionRoomHandlerOld
def sponsoreAcrossPK(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    pkRoomId = msg.body.get('pkRoomId')
    punishment = msg.body.get('punishment', '')
    countdown = msg.body.get('countdown')
    return MicServer.micRoomService.sponsoreAcrossPK(roomId, sessionInfo.userId, pkRoomId, punishment, countdown)


@messageHandler(MsgRoutes.ROOM_REPLY_ACORSS_PK)
@exceptionRoomHandlerOld
def replyAcrossPK(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    pkRoomId = msg.body.get('pkRoomId')
    accept = msg.body.get('accept')
    if accept == 1:
        MicServer.micRoomService.acceptAcrossPK(roomId, sessionInfo.userId, pkRoomId)
    else:
        MicServer.micRoomService.refusedAcrossPK(roomId, sessionInfo.userId, pkRoomId)


@messageHandler(MsgRoutes.ROOM_INVITE_PK_LIST)
@exceptionRoomHandlerOld
def invitePKList(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    MicServer.micRoomService.invitePKList(roomId, sessionInfo.userId)


@messageHandler(MsgRoutes.ROOM_ACORSS_PKING_INFO)
@exceptionRoomHandlerOld
def acorssPKingInfo(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    MicServer.micRoomService.acorssPKingInfo(roomId, sessionInfo.userId)


@messageHandler(MsgRoutes.ROOM_SEARCH_ROOM)
@exceptionRoomHandlerOld
def searchRoom(msg, sessionInfo):
    roomId = msg.body.get('roomId')
    searchId = msg.body.get('searchId')
    MicServer.micRoomService.searchRoom(roomId, sessionInfo.userId, searchId)


# @messageHandler('/user/joinPKLocation')
# @exceptionRoomHandlerOld
# def joinPKLocation(msg, sessionInfo):
#     '''
#     加入团队pk
#     '''
#     roomId = msg.body.get('roomId')
#     teamLocation = msg.body.get('location')
#     return MicServer.micRoomService.joinPKLocation(roomId, sessionInfo.userId, teamLocation)
#
#
# @messageHandler('/user/leavePKLocation')
# @exceptionRoomHandlerOld
# def leavePKLocation(msg, sessionInfo):
#     '''
#     下pk
#     '''
#     roomId = msg.body.get('roomId')
#     return MicServer.micRoomService.leavePKLocation(roomId, sessionInfo.userId, UserLeaveMicReason.USER_ACTIVE)

@messageHandler('/user/invitePKLocation')
@exceptionRoomHandlerOld
def invitePKLocation(msg, sessionInfo):
    '''
    抱上/下pk
    '''
    roomId = msg.body.get('roomId')
    inviteeUserId = msg.body.get('inviteUserId')
    teamLocation = msg.body.get('location')
    cancel = msg.body.get('cancel') == 2
    return MicServer.micRoomService.invitePKLocation(roomId, sessionInfo.userId, inviteeUserId, teamLocation, cancel)


@messageHandler('/user/lockPKLocation')
@exceptionRoomHandlerOld
def lockPKLocation(msg, sessionInfo):
    '''
    锁/取消锁pk
    '''
    roomId = msg.body.get('roomId')
    teamLocation = msg.body.get('location')
    locked = msg.body.get('lock')
    return MicServer.micRoomService.lockPKLocation(roomId, sessionInfo.userId, teamLocation, locked)


@messageHandler('/user/disablePKLocation')
@exceptionRoomHandlerOld
def disablePKLocation(msg, sessionInfo):
    '''
    禁/取消禁pk
    '''
    roomId = msg.body.get('roomId')
    teamLocation = msg.body.get('location')
    disabled = msg.body.get('disable')
    return MicServer.micRoomService.disablePKLocation(roomId, sessionInfo.userId, teamLocation, disabled)


@messageHandler('/user/countdownPKLocation')
@exceptionRoomHandlerOld
def countdownPKLocation(msg, sessionInfo):
    '''
    麦位倒计时
    '''
    roomId = msg.body.get('roomId')
    teamLocation = msg.body.get('location')
    cancel = msg.body.get('cancel')
    if cancel:
        MicServer.micRoomService.cancelCountdownPKLocation(roomId, sessionInfo.userId, teamLocation)
    else:
        duration = msg.body.get('duration')
        MicServer.micRoomService.countdownPKLocation(roomId, sessionInfo.userId, teamLocation, duration)

