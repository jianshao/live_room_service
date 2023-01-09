# -*- coding=utf-8 -*-
'''
Created on 2018年5月22日

@author: zhaojiangang
'''

    
import importlib
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

from tomato.server import server
from tomato.utils import ttlog, ttbilog
from tomato.utils.ttlog import _Formatter
from tomato.utils.ttbilog import _Formatter as _BIFormatter


if sys.getdefaultencoding().lower() != 'utf-8':
    reload(sys)
    mysys = sys
    mysys.setdefaultencoding('utf-8')


def parseStrRedisConf(redisConf):
    parts = redisConf.split(':')
    if len(parts) < 2:
        return None
    return {'host':parts[0], 'port':int(parts[1]), 'db':int(parts[2])}


def main(args):
    if len(args) < 5:
        print 'pypy run.py <serverId> <appModule>, <configPathOrConfigRedis> <logPath>'
        return -1
    
    appArgs = args[5:]

    serverId = args[1]
    appModuleName = args[2]
    configPathOrConfigRedis = args[3]
    
    logsPath = args[4]
    if not os.path.exists(logsPath):
        os.mkdir(logsPath)

    appModule = importlib.import_module(appModuleName)
    
    # 初始化log
    filehandler = TimedRotatingFileHandler('%s/%s.log' % (logsPath, serverId), when='MIDNIGHT', interval=1, backupCount=3)    
    # 设置后缀名称，跟strftime的格式一样  
    filehandler.suffix = '%Y-%m-%d.log'
    formatter = _Formatter('%(asctime)s %(message)s')
    formatter.default_msec_format = '%s.%03d'
    
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)

    ttlog.createLogger(filehandler)
    ttlog.setLevel(ttlog.TRACE)

    # 初始化log
    biFilehandler = TimedRotatingFileHandler('%s/%s.bi.log' % (logsPath, serverId), when='MIDNIGHT', interval=1,
                                           backupCount=3)
    # 设置后缀名称，跟strftime的格式一样
    biFilehandler.suffix = '%Y-%m-%d.log'
    biFormatter = _BIFormatter('')
    biFormatter.default_msec_format = ''

    biFilehandler.setLevel(logging.DEBUG)
    biFilehandler.setFormatter(biFormatter)

    ttbilog.createLogger(biFilehandler)
    ttbilog.setLevel(ttbilog.TRACE)

    redisConf = parseStrRedisConf(configPathOrConfigRedis)
    if redisConf:
        server.runWithRedisConf(serverId, redisConf, appModule.app, appArgs)
    else:
        server.runWithFileConf(serverId, configPathOrConfigRedis, appModule.app, appArgs)


if __name__ == '__main__':
    ret = main(sys.argv)
    exit(ret)


