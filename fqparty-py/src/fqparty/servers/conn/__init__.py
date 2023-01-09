# -*- coding=utf-8 -*-
'''
Created on 2018年3月21日

@author: zhaojiangang
'''
import fqparty
from fqparty import dao
from fqparty.dao.map_dao import MapDao
from fqparty.dao.redis.dao_redis import MapDaoRedis
from fqparty.proxy.user import user_remote_proxy
import tomato
from tomato.conn.message import TTSessionInfo
from tomato.conn.session import TTSessionListener
from tomato.utils import ttlog


class ConnServer(object):
    pass


class SessionListener(TTSessionListener):
    def onSessionOpened(self, session):
        ttlog.info('SessionListener.onSessionOpened',
                   'sessionId=', session.sessionId)
    
    def onSessionBindUser(self, session):
        ttlog.info('SessionListener.onSessionBindUser',
                   'sessionId=', session.sessionId,
                   'userId=', session.userId)
        fqparty.app.userFrontDao.setFrontendId(session.userId, tomato.app.serverId)
    
    def onSessionClosed(self, session, reason):
        ttlog.info('SessionListener.onSessionClosed',
                   'sessionId=', session.sessionId,
                   'userId=', session.userId,
                   'clientHeartbeatTimeout=', session.clientHeartbeatTimeout,
                   'reason=', reason)

        if session.userId:
            # 删除
            fqparty.app.userFrontDao.removeFrontendId(session.userId)
            user_remote_proxy.logout(session.userId, reason)

    def onSessionHeartbeat(self, session, pkg):
        ttlog.info('SessionListener.onSessionHeartbeat',
                   'sessionId=', session.sessionId,
                   'userId=', session.userId,
                   'clientHeartbeatTimeout=', session.clientHeartbeatTimeout)
        
        if session.userId > 0:
            user_remote_proxy.userHeartbeat(session.userId, pkg)


def initServer():
    tomato.app.sessionListener = SessionListener()
    ttlog.info('conn.initServer ok')

def startServer():
    ttlog.info('conn.startServer ok')


