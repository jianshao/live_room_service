# -*- coding:utf-8 -*-
'''
Created on 2019年10月9日

@author: laochao
'''
from demo import router
import tomato


REMOTE_SERVICE_NAME = 'xymatch.user.user_remote'

def login(userId, token):
    '''
    用户登录
    '''
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'login', userId, token)

def logout(userId, reason):
    '''
    用户登录
    '''
    serverId = router.choiceUserServerForUser(userId)
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'logout', userId)


