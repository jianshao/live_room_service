# -*- coding=utf-8 -*-
'''
Created on 2018年1月12日

@author: zhaojiangang
'''

import tomato
from tomato.conn.message import TTMessage, TTSessionInfo
from tomato.decorator.decorator import remoteMethod


__serviceName__ = 'tomato.remote.backend.message_remote'

@remoteMethod()
def forwardMessage(msg, sessionInfo):
    msg = TTMessage().fromDict(msg)
    sessionInfo = TTSessionInfo().fromDict(sessionInfo)
    return tomato.app.messageController.handleMessage(msg, sessionInfo)


