# -*- coding=utf-8 -*-
'''
Created on 2018年1月13日

@author: zhaojiangang
'''
import tomato
from tomato.decorator.decorator import messageHandler


@messageHandler('/user/*')
def bindUser(msg, sessionInfo):
    userId = msg.body.get('userId')
    _token = msg.body.get('token')
    
    tomato.app.sessionManager.bindUser(sessionInfo.sessionId, userId)
    return 'ok'


