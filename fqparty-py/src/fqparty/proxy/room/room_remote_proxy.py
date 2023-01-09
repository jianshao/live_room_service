# -*- coding:utf-8 -*-
'''
Created on 2020年10月31日

@author: zhaojiangang
'''
from fqparty import router
import tomato


REMOTE_SERVICE_NAME = 'fqparty.room.room_remote'

def userHeartbeat(roomId, userId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userHeartbeat', roomId, userId)

def isUserInRoom(roomId, userId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'isUserInRoom', roomId, userId)

def userEnterRoom(roomId, userId, password):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userEnterRoom', roomId, userId, password)

def userLeaveRoom(roomId, userId, reason, reasonInfo=None):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userLeaveRoom',roomId, userId, reason, reasonInfo)

def userOffline(roomId, userId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userOffline',roomId, userId)

def userOnMic(roomId, userId, micId, post=False):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userOnMic', roomId, userId, micId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userOnMic', roomId, userId, micId)

def userLeaveMic(roomId, userId, reason, post=False):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userLeaveMic', roomId, userId, reason)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userLeaveMic', roomId, userId, reason)

def getRoomUserInfo(roomId, userId, queryUserId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getRoomUserInfo', roomId, userId, queryUserId)

def pushRoomInfo(roomId, userId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'pushRoomInfo', roomId, userId)

def getRoomUserList(roomId, userId, listType):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getRoomUserList', roomId, userId, listType)

def getRoomUserListAll(roomId, userId, pageIndex, pageNum):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getRoomUserListAll', roomId, userId,  pageIndex, pageNum)

def getRoomUserListThree(roomId, userId, num):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getRoomUserListThree', roomId, userId,  num)

def getUserMic(roomId, userId):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getUserMic', roomId, userId)

def sendMsgToRoom(roomId, userId, msgType, msg):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'sendMsgToRoom', roomId, userId, msgType, msg)

def syncMusicData(roomId, userId, msg):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'syncMusicData', roomId, userId, msg)

def disableUserMsg(roomId, userId, disabled):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'disableUserMsg', roomId, userId, disabled)

def banRoom(roomId, operator, reasonInfo):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'banRoom', roomId, operator, reasonInfo)

def pushPhpMsgToAllRoomServer(roomId, msg, excludeServerIds, msgType=None):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        if not excludeServerIds or (serverId not in excludeServerIds):
            tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushMsgToRoom', roomId, msg, msgType)

def pushMsgToRoom(roomId, msg, msgType=None):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushMsgToRoom', roomId, msg, msgType)

def pushMsgToAllRoom(msg, excludeRoomIds=[], excludeUserIds=[], msgType=None):
    serverIds = router.getAllRoomServerId()
    for serverId in serverIds:
        tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushMsgToAllRoom', msg, excludeRoomIds, excludeUserIds, msgType)

def lockRoom(roomId, locked):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'lockRoom', roomId, locked)

def updateUserInfo(roomId, userId, post=False):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'updateUserInfo', roomId, userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'updateUserInfo', roomId, userId)

def syncRoomData(roomId, dataType):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'syncRoomData', roomId, dataType)

def sendRoomMsgToRoomServer(serverId, roomId, msg, excludeUserIds, canIgnore=False):
    tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'sendRoomMsg', roomId, msg, excludeUserIds, canIgnore)

def sendRoomMsgToAllRoomServer(roomId, msg, excludeUserIds, excludeServerIds, canIgnore=False):
    serverIds = router.getRoomServerIdsByRoomId(roomId)
    for serverId in serverIds:
        if not excludeServerIds or (serverId not in excludeServerIds):
            sendRoomMsgToRoomServer(serverId, roomId, msg, excludeUserIds, canIgnore)

def sendRoomMsgToUser(roomId, userId, msg):
    serverId = router.choiceRoomServerForUser(roomId, userId)
    if serverId == tomato.app.serverId:
        return

    tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'sendRoomMsgToUser', roomId, userId, msg)
    
    
    