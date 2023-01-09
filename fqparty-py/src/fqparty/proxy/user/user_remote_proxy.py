# -*- coding:utf-8 -*-
'''
Created on 2020年10月30日

@author: zhaojiangang
'''
from fqparty import router
import tomato


REMOTE_SERVICE_NAME = 'fqparty.user.user_remote'

def login(userId, sessionInfo):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'login', userId, sessionInfo)

def loginAndEnterRoom(userId, roomId, sessionInfo, password):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'loginAndEnterRoom', userId, roomId, sessionInfo, password)

def kickoutRoomUser(userId, roomId):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'kickoutRoomUser', userId, roomId)

def userEnterRoom(userId, roomId, password):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userEnterRoom', userId, roomId, password)

def userLeaveRoom(userId, roomId, reason, post=False):
    serverId = router.choiceUserServerForUser(userId)
    if post:
        return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userLeaveRoom', userId, roomId, reason)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'userLeaveRoom', userId, roomId, reason)

def logout(userId, reason):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'logout', userId, reason)

def userHeartbeat(userId, pkg):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'userHeartbeat', userId, pkg)

def getUserRoomLocation(userId):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getUserRoomLocation', userId)

def updateUserInfo(userId):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'updateUserInfo', userId)

def getUserInfo(userId):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'getUserInfo', userId)

def globalUserNotify(userId, msg):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'globalUserNotify', userId, msg)

def checkUserLogin(userId, msg):
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'checkUserLogin', userId, msg)

