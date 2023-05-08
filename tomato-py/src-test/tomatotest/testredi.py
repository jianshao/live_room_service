# -*- coding:utf-8 -*-
'''
Created on 2020年11月10日

@author: zhaojiangang
'''
from tomato.core import mainloop
from tomato.db import redis

def main():
    conn = redis.client.connectRedis('182.92.186.104', 6379, 2, 'Etang123')
    print('conn=', conn)
    print(conn.send('keys', '*'))


if __name__ == '__main__':
    mainloop.run(main)
    