# -*- coding=utf-8 -*-
'''
Created on 2016年12月1日

@author: zjgzzz@126.com
'''

import time
 
from tomato.conn.client import TTConnectionClient
from tomato.conn.message import TTMessageCodecJson
from tomato.core import reactor, mainloop
from tomato.utils import ttlog
  
  
def main():
    try:
        client1 = TTConnectionClient(TTMessageCodecJson(), 6)
        reactor.connectTCP('127.0.0.1', 9100, client1, 1)
        count = 1
        resp = client1.sendRequest('/user/bind', {'userId':10001}).get()
        ttlog.info('bindUser resp=', resp)
        if 'ok' == resp:
            t = time.time()
            for _ in xrange(count):
                future = client1.sendRequest('/str/upper', {'userId':10001, 'string':'hello'})
                try:
                    resp = future.get()
                    ttlog.info('strUpper resp=', resp)
                except:
                    ttlog.error()
            ttlog.info('run', count, 'request use', time.time() - t, 'S')
            
            client1.sendRequest('/user/unbind', {})
    finally:
        mainloop.stop()
  
  
if __name__ == '__main__':
    mainloop.run(main)
    
