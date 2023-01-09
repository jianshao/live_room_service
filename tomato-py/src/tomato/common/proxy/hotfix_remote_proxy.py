# -*- coding=utf-8 -*-
'''
Created on 2018年6月11日

@author: zhaojiangang
'''
import tomato
from tomato.config import configure

REMOTE_SERVICE_NAME = 'tomato.remote.all.hotfix_remote'


def reloadConfig(serverIds):
    serverIds = serverIds.split(',')
    for serverId in serverIds:
        if serverId == tomato.app.serverId:
            configure.reloadConf(module=None)
        else:
            _reloadConfig(serverId)


def _reloadConfig(serverId):
    return tomato.app.rpcCall(serverId, REMOTE_SERVICE_NAME, 'reloadConfig')
