# -*- coding=utf-8 -*-
'''
Created on 2017年12月16日

@author: zhaojiangang
'''

import logging
from logging.handlers import TimedRotatingFileHandler

from demo import router
import tomato
from tomato.config import configure
from tomato.core import mainloop
from tomato.decorator import decorator
from tomato.utils import ttlog
from tomato.utils.ttlog import _Formatter


def main(serverId, configFilePath):
    try:
        print '>>> mmain'
        # 初始化log
        filehandler = TimedRotatingFileHandler('%s/%s.log' % ('./', serverId), when='MIDNIGHT', interval=1, backupCount=3)    
        # 设置后缀名称，跟strftime的格式一样  
        filehandler.suffix = '%Y-%m-%d.log'
        formatter = _Formatter('%(asctime)s %(message)s')
        formatter.default_msec_format = '%s.%03d'
        
        filehandler.setLevel(logging.DEBUG)
        filehandler.setFormatter(formatter)
    
        ttlog.createLogger(filehandler)
#         ttlog.addHandler(filehandler)
        ttlog.setLevel(ttlog.TRACE)

        configure.initByFile(configFilePath)
        app = tomato.app
        app.init(serverId)
        app.routeController.setRouteFuncByServerType('user', router.routeUser)
        decorator.loadServerPackageDecorator(app, 'tomatotest.app.servers')
        tomato.app.start()
    except:
        ttlog.error('main', serverId, configFilePath)
        mainloop.stop()


def run(serverId, configFilePath):
    print '>>> run', serverId, configFilePath
    mainloop.run(main, serverId, configFilePath)


