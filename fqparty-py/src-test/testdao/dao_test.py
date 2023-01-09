# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''
import time

from fqparty.dao.redis.dao_redis import ActiveUserDaoRedis
from fqparty.domain.user.user import ActiveUser
from tomato.core import mainloop
from tomato.db.redis import client


def main():
    conn = client.connectRedis('127.0.0.1', 6379, 0)
    dao = ActiveUserDaoRedis([conn])
    serverId = 'US000001'
    dao.saveActiveUser(serverId, ActiveUser(10001, int(time.time())))
    print dao.loadAllActiveUser('US000001')
    mainloop.stop()

if __name__ == '__main__':
    mainloop.run(main)


