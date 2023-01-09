# -*- coding=utf-8 -*-
'''
Created on 2018年3月19日

@author: zhaojiangang
'''

from tomato.server import server
import fanqieyy


if __name__ == '__main__':
    configRootPath = '/Users/zhaojiangang/zjg/dev/workspaces/server/eclipse/fanqie/fanqieyy-conf/dev'
    server.runWithFileConf('CO000001', configRootPath, fanqieyy.app)


