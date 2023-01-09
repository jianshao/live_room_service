# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty.decorator.decorator import remoteExceptionHandler
from fqparty.domain.models.user import User
from fqparty.proxy.mic import mic_remote_proxy
from fqparty.servers.mic import MicServer
from tomato.decorator.decorator import remoteMethod


__serviceName__ = mic_remote_proxy.REMOTE_SERVICE_NAME

@remoteMethod()
@remoteExceptionHandler
def userHeartbeat(roomId, userId):
    MicServer.micRoomService.userHeartbeat(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def userLeaveRoom(roomId, userId, reason):
    MicServer.micRoomService.userLeaveRoom(roomId, userId, reason)

@remoteMethod()
@remoteExceptionHandler
def userOnMic(roomId, userDict, micId):
    user = User().fromDict(userDict)
    return MicServer.micRoomService.userOnMic(roomId, user, micId)

@remoteMethod()
@remoteExceptionHandler
def userLeaveMic(roomId, userId, reason):
    return MicServer.micRoomService.userLeaveMic(roomId, userId, reason)

@remoteMethod()
@remoteExceptionHandler
def onUserLeaveRoom(roomId, userId, reason):
    return MicServer.micRoomService.userLeaveMic(roomId, userId, reason, True)

@remoteMethod()
@remoteExceptionHandler
def joinPKLocation(roomId, userDict, location):
    user = User().fromDict(userDict)
    return MicServer.micRoomService.joinPKLocation(roomId, user, location)

@remoteMethod()
@remoteExceptionHandler
def leavePKLocation(roomId, userId, reason):
    '''
    下pk
    '''
    return MicServer.micRoomService.leavePKLocation(roomId, userId, reason)

@remoteMethod()
@remoteExceptionHandler
def lockMic(roomId, userId, micId, locked):
    MicServer.micRoomService.lockMic(roomId, userId, micId, locked)

@remoteMethod()
@remoteExceptionHandler
def disableMic(roomId, userId, micId, reason):
    MicServer.micRoomService.disableMic(roomId, userId, micId, reason)

@remoteMethod()
@remoteExceptionHandler
def inviteMic(roomId, userId, inviteeUserId, micId, cancel):
    MicServer.micRoomService.inviteMic(roomId, userId, inviteeUserId, micId, cancel)

@remoteMethod()
@remoteExceptionHandler
def countdownMic(roomId, userId, micId, duration):
    MicServer.micRoomService.countdownMic(roomId, userId, micId, duration)

@remoteMethod()
@remoteExceptionHandler
def cancelCountdownMic(roomId, userId, micId):
    MicServer.micRoomService.cancelCountdownMic(roomId, userId, micId)

@remoteMethod()
@remoteExceptionHandler
def startPK(roomId, userId, redList, blueList, punishment, countdown):
    MicServer.micRoomService.startPK(roomId, userId, redList, blueList, punishment, countdown)

@remoteMethod()
@remoteExceptionHandler
def endPK(roomId, userId):
    MicServer.micRoomService.endPK(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def endAcrossPK(roomId):
    MicServer.micRoomService.innerEndAcrossPK(roomId)

@remoteMethod()
@remoteExceptionHandler
def innerStartAcrossPK(roomId, createRoomId, pkRoomId, punishment, countdown):
    MicServer.micRoomService.innerStartAcrossPK(roomId, createRoomId, pkRoomId, punishment, countdown)

@remoteMethod()
@remoteExceptionHandler
def addPKCountdown(roomId, userId, duration):
    MicServer.micRoomService.addPKCountdown(roomId, userId, duration)

@remoteMethod()
@remoteExceptionHandler
def updatePKRoomData(roomId, pkMap, contributeMap):
    MicServer.micRoomService.updatePKRoomData(roomId, pkMap, contributeMap)

@remoteMethod()
@remoteExceptionHandler
def notifyRoomSponsored(roomId):
    MicServer.micRoomService.notifyRoomSponsored(roomId)

@remoteMethod()
@remoteExceptionHandler
def notifyRoomAcrossPKStart(roomId, acrossPKData, pkRoomInfo):
    MicServer.micRoomService.notifyRoomAcrossPKStart(roomId, acrossPKData, pkRoomInfo)

@remoteMethod()
@remoteExceptionHandler
def acorssPKingInfo(roomId, userId):
    MicServer.micRoomService.acorssPKingInfo(roomId, userId)

@remoteMethod()
@remoteExceptionHandler
def pushMsgToMicRoom(roomId, msg):
    MicServer.micRoomService.pushMsgToRoom(roomId, msg)

@remoteMethod()
@remoteExceptionHandler
def loadMicRoom(roomId):
    MicServer.micRoomService.loadMicRoom(roomId)

@remoteMethod()
@remoteExceptionHandler
def removeMicRoom(roomId):
    MicServer.micRoomService.removeMicRoom(roomId)

@remoteMethod()
@remoteExceptionHandler
def syncMicRoomData(roomId, dataType):
    MicServer.micRoomService.updateRoomData(roomId, dataType)

@remoteMethod()
@remoteExceptionHandler
def sendEmoticon(roomId, userDict, msg):
    user = User().fromDict(userDict)
    MicServer.micRoomService.sendEmoticon(roomId, user, msg)

@remoteMethod()
@remoteExceptionHandler
def banRoom(roomId, operator, reasonInfo):
    MicServer.micRoomService.banRoom(roomId, operator, reasonInfo)

#################################################
@remoteMethod()
@remoteExceptionHandler
def disableRoomMsg(roomId, userId, disabled):
    MicServer.micRoomService.disableRoomMsg(roomId, userId, disabled)


