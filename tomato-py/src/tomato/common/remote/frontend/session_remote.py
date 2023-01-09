# -*- coding=utf-8 -*-
'''
Created on 2018年1月12日

@author: zhaojiangang
'''
import tomato
from tomato.common.proxy import session_remote_proxy
from tomato.conn.message import TTMessage
from tomato.decorator.decorator import remoteMethod
from tomato.utils import ttlog


__serviceName__ = session_remote_proxy.REMOTE_SERVICE_NAME


@remoteMethod()
def pushMessage(msg, userIds, canIgnore=False):
    if not isinstance(userIds, list):
        userIds = [userIds]
    for userId in userIds:
        session = tomato.app.sessionManager.findSessionByUserId(userId)
        if session:
            if not canIgnore or session.canSend(msg):
                ttmsg = TTMessage().fromDict(msg)
                session.sendMessage(ttmsg)
            else:
                ttlog.warn('session_remote.pushMessage ignore',
                           'userId=', userId,
                           'sessionId=', session.sessionId)
        else:
            ttlog.warn('Not found session for userId %s' % (userId))

@remoteMethod()
def pushRawData(data, userIds, canIgnore=False):
    if not isinstance(userIds, list):
        userIds = [userIds]
    for userId in userIds:
        session = tomato.app.sessionManager.findSessionByUserId(userId)
        if session:
            if not canIgnore or session.canSend(data):
                session.sendRaw(data)
            else:
                ttlog.warn('session_remote.pushRawData ignore',
                           'userId=', userId,
                           'sessionId=', session.sessionId)
        else:
            ttlog.warn('Not found session for userId %s' % (userId))

def kickSessionLocal(userId, msg, reason):
    assert(not msg or isinstance(msg, TTMessage))
    session = tomato.app.sessionManager.findSessionByUserId(userId)
    if session:
        ttlog.info('session_remote.kickSessionLocal',
                   'userId=', userId,
                   'sessionId=', session.sessionId,
                   'msg=', msg,
                   'reason=', reason)
        tomato.app.sessionManager.kickSession(session.sessionId, msg, reason)
        return True
    return False

@remoteMethod()
def kickSession(userId, msg, reason):
    if msg is not None:
        msg = TTMessage().fromDict(msg)
    kickSessionLocal(userId, msg, reason)



