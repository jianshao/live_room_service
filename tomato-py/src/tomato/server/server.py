# -*- coding=utf-8 -*-
'''
Created on 2018年5月3日

@author: zhaojiangang
'''

import tomato
from tomato.config import configure
from tomato.core import mainloop
from tomato.utils import ttlog


def _runWithFileConf(serverId, confRootPath, app, appArgs):
    try:
        configure.initByFile(confRootPath)
        logLevel = configure.loadJson('server.tomato.global', {}).get('log', {}).get('level', ttlog.INFO)
        ttlog.setLevel(logLevel)
        tomato.app.appArgs = appArgs
        tomato.app.init(serverId)
        app.init()
        app.start()
        tomato.app.start()
    except:
        ttlog.error('server._runWithFileConf',
                    'serverId=', serverId,
                    'app=', app,
                    'appArgs=', appArgs)
        mainloop.stop()

def runWithFileConf(serverId, confRootPath, app, appArgs):
    ttlog.info('server.runWithFileConf',
               'serverId=', serverId,
               'app=', app,
               'appArgs=', appArgs)
    mainloop.run(_runWithFileConf, serverId, confRootPath, app, appArgs)

def _runWithRedisConf(serverId, redisConf, app, appArgs):
    try:
        configure.initByRedis(redisConf['host'], redisConf['port'], redisConf['db'])
        logLevel = configure.loadJson('server.tomato.global', {}).get('log', {}).get('level', ttlog.INFO)
        ttlog.setLevel(logLevel)
        tomato.app.appArgs = appArgs
        tomato.app.init(serverId)
        app.init()
        app.start()
        tomato.app.start()
    except:
        ttlog.error('server._runWithRedisConf',
                    'serverId=', serverId,
                    'app=', app,
                    'appArgs=', appArgs)
        mainloop.stop()

def runWithRedisConf(serverId, redisConf, app, appArgs=[]):
    ttlog.info('server.runWithRedisConf',
               'serverId=', serverId,
               'redisConf=', redisConf,
               'app=', app,
               'appArgs=', appArgs)
    mainloop.run(_runWithRedisConf, serverId, redisConf, app, appArgs)


