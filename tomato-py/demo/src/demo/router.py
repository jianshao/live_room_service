# -*- coding=utf-8 -*-
'''
Created on 2018年1月13日

@author: zhaojiangang
'''
import tomato


def routeUser(serverType, msg, sessionInfo):
    userId = sessionInfo.userId
    if not userId:
        userId = msg.body.get('userId')
    serverInfos = tomato.app.getServerInfosByServerType(serverType)
    return serverInfos[userId % len(serverInfos)]['serverId']

def choiceUserServerForUser(userId):
    serverInfos = tomato.app.getServerInfosByServerType('user')
    return serverInfos[userId % len(serverInfos)]['serverId']


