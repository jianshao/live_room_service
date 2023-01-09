# -*- coding=utf-8 -*-
'''
Created on 2018年6月23日

@author: zhaojiangang
'''
import random
import time
import uuid

from tomato.utils.orderdedict import TTOrderedDict


class Session():
    def __init__(self, sid):
        self.sid = sid
        self.value = sid

def kick():
    pass


def testOrderDict():
    d = TTOrderedDict()
    sids = []
    for i in xrange(5000):
        sid = uuid.uuid1().get_hex()
        session = Session(sid)
        d[sid] = session
        sids.append(sid)
    
    random.shuffle(sids)
    
    st = time.time()
    for i in xrange(5000):
        session = d[sids[i]]
        d[session.sid] = session
    et = time.time()
    print 'used', et - st
    st = time.time()
    for _ in d.values():
        kick()
    et = time.time()
    print 'used', et - st
        
        
if __name__ == '__main__':
    testOrderDict()
    
    