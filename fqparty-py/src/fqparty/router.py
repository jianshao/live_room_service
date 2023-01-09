# -*- coding=utf-8 -*-
'''
Created on 2018年3月24日

@author: zhaojiangang
'''
import fqparty
from fqparty import const
import tomato
from tomato.core.exceptions import TTException
from tomato.utils import ttlog
from tomato.config import configure


def serverSplit(serverInfos, n):
    return [serverInfos[i:i+n] for i in range(0, len(serverInfos), n)]

def getRoomServerIdByServerInfos(serverInfos, roomId, userId):
    roomGroupCount = configure.loadJson('server.fqparty.global', {}).get('roomGroupCount', 2)
    groupCount = len(serverInfos) / roomGroupCount
    newServerss = serverSplit(serverInfos, groupCount)
    newServers = newServerss[int(userId) % roomGroupCount]

    if ttlog.isDebugEnabled():
        ttlog.debug('router.getRoomServerIdByServerInfos',
                    'roomId=', roomId,
                    'roomGroupCount=', roomGroupCount,
                    'groupCount=', groupCount,
                    'newServerss=', newServerss,
                    'newServers=', newServers,
                    'serverInfos=', len(serverInfos))

    return newServers[int(roomId) % len(newServers)]['serverId']

def choiceUserServerForUser(userId):
    serverInfos = tomato.app.getServerInfosByServerType(const.ServerTypes.USER)
    if ttlog.isDebugEnabled():
        ttlog.debug('router.choiceUserServerForUser',
                    'userId=', userId,
                    'serverInfos=', serverInfos)
    return serverInfos[int(userId) % len(serverInfos)]['serverId']

def choiceRoomServerForUser(roomId, userId):
    serverInfos = tomato.app.getServerInfosByServerType(const.ServerTypes.ROOM)
    if ttlog.isDebugEnabled():
        ttlog.debug('router.choiceRoomServerForUser',
                    'roomId=', roomId,
                    'userId=', userId,
                    'serverInfos=', serverInfos)

    return serverInfos[int(userId) % len(serverInfos)]['serverId']

def choiceMicServerForUser(roomId):
    serverInfos = tomato.app.getServerInfosByServerType(const.ServerTypes.MIC)
    if ttlog.isDebugEnabled():
        ttlog.debug('router.choiceMicServerForUser',
                    'roomId=', roomId,
                    'serverInfos=', serverInfos)
    return serverInfos[int(roomId) % len(serverInfos)]['serverId']

def getRoomServerIdsByRoomId(roomId):
    return getAllRoomServerId()
    
    # serverInfos = tomato.app.getServerInfosByServerType(const.ServerTypes.ROOM)
    #
    # roomGroupCount = configure.loadJson('server.fqparty.global', {}).get('roomGroupCount', 0)
    # groupCount = len(serverInfos) / roomGroupCount
    # newServerss = serverSplit(serverInfos, groupCount)
    # serverIds = []
    # for newServers in newServerss:
    #     si = newServers[int(roomId) % len(newServers)]
    #     serverIds.append(si['serverId'])
    #
    # if ttlog.isDebugEnabled():
    #     ttlog.debug('router.getAllRoomServerId',
    #                 'roomGroupCount=', roomGroupCount,
    #                 'groupCount=', groupCount,
    #                 'serverInfos=', len(serverInfos),
    #                 'serverIds=', serverIds,
    #                 'newServerss=', newServerss)
    #
    # return serverIds

def getAllRoomServerId():
    serverInfos = tomato.app.getServerInfosByServerType(const.ServerTypes.ROOM)
    if ttlog.isDebugEnabled():
        ttlog.debug('router.getAllRoomServerId',
                    'serverInfos=', serverInfos)

    return [si['serverId'] for si in serverInfos]

def routeUser(serverType, msg, sessionInfo):
    userId = sessionInfo.userId
    if not userId:
        userId = msg.body.get('userId')
    serverInfos = tomato.app.getServerInfosByServerType(serverType)
    return serverInfos[int(userId) % len(serverInfos)]['serverId']

def routeRoom(serverType, msg, sessionInfo):
    roomId = msg.body.get('roomId')
    if not roomId:
        raise TTException(-1, 'Not found roomId in msg')
    userId = sessionInfo.userId
    if not userId:
        userId = msg.body.get('userId')
    return choiceRoomServerForUser(roomId, userId)

def routeMic(serverType, msg, sessionInfo):
    roomId = msg.body.get('roomId')
    if not roomId:
        raise TTException(-1, 'Not found roomId in msg')
    return choiceMicServerForUser(roomId)

