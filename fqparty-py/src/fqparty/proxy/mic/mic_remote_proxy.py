# -*- coding:utf-8 -*-
'''
Created on 2020年10月31日

@author: zhaojiangang
'''
from fqparty import router
import tomato


REMOTE_SERVICE_NAME = 'fqparty.room.mic_remote'

def userHeartbeat(roomId, userId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userHeartbeat', roomId, userId)

def userOnMic(roomId, userDict, micId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userOnMic', roomId, userDict, micId)

def userLeaveMic(roomId, userId, reason, post=False):
    serverId = router.choiceMicServerForUser(roomId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userLeaveMic', roomId, userId, reason)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userLeaveMic', roomId, userId, reason)

def onUserLeaveRoom(roomId, userId, reason):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'onUserLeaveRoom', roomId, userId, reason)

def joinPKLocation(roomId, userDict, location):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'joinPKLocation', roomId, userDict, location)

def leavePKLocation(roomId, userId, reason, post=False):
    serverId = router.choiceMicServerForUser(roomId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'leavePKLocation', roomId, userId, reason)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'leavePKLocation', roomId, userId, reason)

def lockMic(roomId, userId, micId, locked):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'lockMic', roomId, userId, micId, locked)

def disableMic(roomId, userId, micId, disabled):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'disableMic', roomId, userId, micId, disabled)

def inviteMic(roomId, userId, inviteeUserId, micId, cancel):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'inviteMic', roomId, userId, inviteeUserId, micId, cancel)

def countdownMic(roomId, userId, micId, duration):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'countdownMic', roomId, userId, micId, duration)

def cancelCountdownMic(roomId, userId, micId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'cancelCountdownMic', roomId, userId, micId)

def sendEmoticon(roomId, userDict, msg):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'sendEmoticon', roomId, userDict, msg)

def startPK(roomId, userId, redList, blueList, punishment, countdown):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'startPK', roomId, userId, redList, blueList, punishment, countdown)

def endPK(roomId, userId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'endPK', roomId, userId)

def endAcrossPK(roomId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'endAcrossPK', roomId)

def innerStartAcrossPK(roomId, createRoomId, pkRoomId, punishment, countdown):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'innerStartAcrossPK', roomId, createRoomId, pkRoomId, punishment, countdown)

def addPKCountdown(roomId, userId, duration):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'addPKCountdown', roomId, userId, duration)

def updatePKRoomData(roomId, pkMap, contributeMap):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'updatePKRoomData', roomId, pkMap, contributeMap)

def notifyRoomAcrossPKStart(roomId, acrossPKData, pkRoomInfo):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'notifyRoomAcrossPKStart', roomId, acrossPKData, pkRoomInfo)

def notifyRoomSponsored(roomId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'notifyRoomSponsored', roomId)

def searchRoom(roomId, userId, searchId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'searchRoom', roomId, userId, searchId)

def pushMsgToRoom(roomId, msg):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushMsgToMicRoom', roomId, msg)

def loadMicRoom(roomId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'loadMicRoom', roomId)

def removeMicRoom(roomId):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'removeMicRoom', roomId)

def syncRoomData(roomId, dataType):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'syncMicRoomData', roomId, dataType)

def banRoom(roomId, operator, reasonInfo):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'banRoom', roomId, operator, reasonInfo)

def disableRoomMsg(roomId, userId, disabled):
    serverId = router.choiceMicServerForUser(roomId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'disableRoomMsg', roomId, userId, disabled)


