# -*- coding:utf-8 -*-
'''
Created on 2020年11月9日

@author: zhaojiangang
'''
import random


def test():
    ret = []
    for _ in xrange(10):
        ret.append(random.randint(1, 10))
        
    print ret
    
if __name__ == '__main__':
    for _ in xrange(10):
        test()
    
    