# -*- coding:utf-8 -*-
'''
Created on 2020年11月10日

@author: zhaojiangang
'''
from fqparty import dao
from tomato.config import configure
from tomato.core import reactor, mainloop


def main():
    configure.initByFile('/Users/zhaojiangang/yuyin/code/py/fanqie/fqparty-conf/dev')
    conns = dao.getRedisConns('common')[0]
    print conns.send('get', 'huaban_1001351')
    subs = dao.get
    reactor.stop()


if __name__ == '__main__':
    mainloop.run(main)