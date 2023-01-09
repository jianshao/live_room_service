# -*- coding:utf-8 -*-
'''
Created on 2020年10月30日

@author: zhaojiangang
'''
from fqparty.const import ErrorCode, MsgRoutes
from fqparty.decorator.decorator import exceptionHandler
from fqparty.proxy.user import user_remote_proxy
# from fqparty.servers.conn import ConnServer
import tomato
from tomato.common.proxy import session_remote_proxy
from tomato.common.remote.frontend import session_remote
from tomato.core.exceptions import TTException
from tomato.decorator.decorator import messageHandler
from tomato.utils import ttlog, strutil
import fqparty
from tomato.const import ConnLostReason
from tomato.core.tasklet import TTTasklet


class BindUserCommand(object):
    def __init__(self, msg):
        self.msg = msg
        self.body = msg.body

    @property
    def userId(self):
        return self.body.get('userId')
    
    @property
    def token(self):
        return self.body.get('token')

    @property
    def deviceInfo(self):
        return self.body.get('deviceInfo', {})

    def validate(self):
        pass


class BindUserAndEnterRoomCommand(object):
    def __init__(self, msg):
        self.msg = msg
        self.userId = 0
        self.body = msg.body

    @property
    def roomId(self):
        return self.body.get('roomId')

    @property
    def token(self):
        return self.body.get('authToken')

    @property
    def password(self):
        return self.body.get('password')

    @property
    def version(self):
        return self.body.get('version')
    
    @property
    def platform(self):
        return self.body.get('platform')
    
    def validate(self):
        pass
        

def kickOldSession(userId, msg):
    frontId = fqparty.app.userFrontDao.getFrontendId(userId)
    if ttlog.isDebugEnabled():
        ttlog.debug('kickOldSession', userId, frontId)
    if frontId:
        if frontId == tomato.app.serverId:
            session_remote.kickSessionLocal(userId, msg, ConnLostReason.CONN_KICKOUT)
        else:
            si = tomato.app.getServerInfoByServerId(frontId)
            if si:
                session_remote_proxy.kickSession(frontId, userId, msg, ConnLostReason.CONN_KICKOUT)


def getKickMsg():
    '''
    获取踢下线消息
    '''
    return None


@messageHandler(MsgRoutes.USER_BIND)
@exceptionHandler
def userBind(msg, sessionInfo):
    '''
    用户绑定长连接
    @return: 用户游戏数据
    '''
    cmd = BindUserCommand(msg)
    try:
        cmd.validate()
        if cmd.userId != fqparty.app.utilService.getUserIdByToken(cmd.token):
            raise TTException(ErrorCode.AUTH_TOKEN_FAILED)
        
        # 踢掉老的session
        kickOldSession(cmd.userId, getKickMsg())
        
        # 绑定userId到长连接
        tomato.app.sessionManager.bindUser(sessionInfo.sessionId, cmd.userId)
        
        sessionDict = {
            'sessionId':sessionInfo.sessionId,
            'frontendId':sessionInfo.frontId,
            'clientIp':sessionInfo.clientIp,
            'clientInfo':cmd.deviceInfo,
            'token': cmd.token
        }

        # 用户登录
        ec, resp = user_remote_proxy.login(cmd.userId, sessionDict)
        if ec != 0:
            raise TTException(-1, resp)
        
        return resp
    except TTException, e:
        ttlog.error('Bind user error', cmd.userId)
        TTTasklet.createTasklet(tomato.app.sessionManager.kickSession, sessionInfo.sessionId, None)
#         tomato.app.sessionManager.kickSession(sessionInfo.sessionId, None)
        return {'ec':e.errorCode, 'info':e.message}
    except:
        ttlog.error('Bind user error', cmd.userId)
#         tomato.app.sessionManager.kickSession(sessionInfo.sessionId, None)
        TTTasklet.createTasklet(tomato.app.sessionManager.kickSession, sessionInfo.sessionId, None)
        return {'ec':ErrorCode.OP_FAILED, 'info':'System error'}


def needCancelServerHeartbeatTimer(sessionDict):
    return False

def _userBindAndEnterRoom(msg, sessionInfo):
    cmd = BindUserAndEnterRoomCommand(msg)
    try:
        userId = fqparty.app.utilService.getUserIdByToken(cmd.token)
        if not userId or userId <= 0:
            raise TTException(ErrorCode.AUTH_TOKEN_FAILED)
        
        cmd.userId = userId

        cmd.validate()
        
        # 踢掉老的session
        kickOldSession(cmd.userId, getKickMsg())
        
        # 绑定userId到长连接
        tomato.app.sessionManager.bindUser(sessionInfo.sessionId, cmd.userId)

        sessionDict = {
            'sessionId':sessionInfo.sessionId,
            'frontendId':sessionInfo.frontId,
            'clientIp':sessionInfo.clientIp,
            'clientInfo':{
                'platform':cmd.platform,
                'version':cmd.version
            },
            'onMicForLogout': msg.body.get('onMicForLogout'),
            'token': cmd.token,
            'old':1
        }
        
        # 用户登录
        ec, resp = user_remote_proxy.loginAndEnterRoom(cmd.userId, cmd.roomId, sessionDict, cmd.password)
        if ec != 0:
            raise TTException(ec, resp)

        session = tomato.app.sessionManager.findSession(sessionInfo.sessionId)
        if session:
            if needCancelServerHeartbeatTimer(sessionDict):
                session.cancelHeartbeatTimer()
            session.sendRaw(strutil.jsonDumps({'msgId':1, 'code':0, 'roomId':0, 'desc':''}))
        return resp
    except TTException, e:
        ttlog.warn('Bind user error',
                   'sessionId=', sessionInfo.sessionId,
                   'userId=', cmd.userId,
                   'roomId=', cmd.roomId,
                   'ex=', '%s:%s' % (e.errorCode, e.message))
        session = tomato.app.sessionManager.findSession(sessionInfo.sessionId)
        if session:
            session.sendRaw(strutil.jsonDumps({'msgId':1, 'code':e.errorCode, 'roomId':0, 'desc':e.message}))
        tomato.app.sessionManager.kickSession(sessionInfo.sessionId, None, ConnLostReason.CONN_LOST)
        return None
    except:
        ttlog.error('Bind user error',
                    'sessionId=', sessionInfo.sessionId,
                    'userId=', cmd.userId,
                    'roomId=', cmd.roomId)
        session = tomato.app.sessionManager.findSession(sessionInfo.sessionId)
        if session:
            session.sendRaw(strutil.jsonDumps({'msgId':1, 'code':1, 'roomId':0, 'desc':''}))
        tomato.app.sessionManager.kickSession(sessionInfo.sessionId, None, ConnLostReason.CONN_LOST)
        return None


@messageHandler(MsgRoutes.USER_BIND_AND_ENTER_ROOM)
@exceptionHandler
def userBindAndEnterRoom(msg, sessionInfo):
    '''
    用户绑定长连接
    @return: 用户游戏数据
    '''
    return _userBindAndEnterRoom(msg, sessionInfo)


