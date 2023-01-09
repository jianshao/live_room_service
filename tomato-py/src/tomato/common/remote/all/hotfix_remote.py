# -*- coding=utf-8 -*-
'''
Created on 2018年1月22日

@author: zhaojiangang
'''
from tomato.utils import ttlog
from tomato.config import configure
from tomato.decorator.decorator import remoteMethod
from tomato.common.proxy import hotfix_remote_proxy

__serviceName__ = hotfix_remote_proxy.REMOTE_SERVICE_NAME


@remoteMethod()
def hotfix(pypath, params):
    return _doHotfix(pypath, params)


def _doHotfix(pypath, params):
    return {'ec': 0, 'pypath': pypath, 'params': params}


@remoteMethod()
def reloadConfig():
    ttlog.info('hotfix_remote reloadConfig')
    configure.reloadConf(module=None)
