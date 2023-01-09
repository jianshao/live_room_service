# -*- coding=utf-8 -*-
'''
Created on 2018年6月11日

@author: zhaojiangang
'''
import tomato


REMOTE_SERVICE_NAME = 'tomato.remote.frontend.session_remote'

def pushMessage(msg, serverId, userIds, canIgnore=False):
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushMessage', msg.toDict(), userIds, canIgnore)

def pushRawData(data, serverId, userIds, canIgnore=False):
    return tomato.app.rpcPost(serverId, REMOTE_SERVICE_NAME, 'pushRawData', data, userIds, canIgnore)

def kickSession(frontId, userId, msg, reason, post=False):
    msg = msg.toDict() if msg else None
    if post:
        return tomato.app.rpcPost(frontId, REMOTE_SERVICE_NAME, 'kickSession', userId, msg, reason)
    return tomato.app.rpcCall(frontId, REMOTE_SERVICE_NAME, 'kickSession', userId, msg, reason)


