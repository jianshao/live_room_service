# -*- coding:utf-8 -*-
'''
Created on 2016年12月21日

@author: zhaojiangang
'''
from collections import OrderedDict
import time


class TTOrderedDict(OrderedDict):
    def frontitem(self):
        it = dict.__iter__(self)
        try:
            k = it.next()
        except StopIteration:
            raise KeyError('dictionary is empty')
        return (k, self.get(k))
    
    def frontitemN(self, n, last=True):
        assert(n > 0 and len(self) >= n)
        ret = []
        for _, v in self.iteritems():
            if len(ret) >= n:
                break
            ret.append(v)
        return ret
    
    def popN(self, n):
        assert(len(self) >= n)
        ret = []
        for _ in xrange(n):
            _, v = self.popitem()
            ret.append(v)
        return ret
        
    def __setitem__(self, key, value):
        try:
            del self[key]
        except:
            pass
        OrderedDict.__setitem__(self, key, value)


if __name__ == '__main__':
    od = TTOrderedDict()
    curTime = time.time()
    od['1'] = curTime + 1
    od['2'] = curTime + 2
    od['3'] = curTime + 3
    od['1'] = curTime + 1
    for k, v in od.iteritems():
        print k, v
    