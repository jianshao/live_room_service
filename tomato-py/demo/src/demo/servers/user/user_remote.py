# -*- coding=utf-8 -*-
'''
Created on 2018年1月13日

@author: zhaojiangang
'''
from tomato.decorator.decorator import remoteMethod
from tomato.utils import ttlog
from demo.proxy.user import user_remote_proxy


__serviceName__ = user_remote_proxy.REMOTE_SERVICE_NAME


@remoteMethod()
def login(userId, token):
    ttlog.info('User login', userId, token)
    return 'ok'


@remoteMethod()
def logout(userId):
    ttlog.info('User logout', userId)
    return 'ok'


