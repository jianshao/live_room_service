# -*- coding=utf-8 -*-
'''
Created on 2018年3月12日

@author: zhaojiangang
'''
import time

from tomato.utils.orderdedict import TTOrderedDict


class TTCache(object):
    def set(self, key, value):
        '''
        添加key, value到缓存
        '''
        raise NotImplementedError
    
    def get(self, key):
        '''
        根据key获取value
        '''
        raise NotImplementedError
    
    def remove(self, key):
        '''
        从缓存中删除
        '''
        raise NotImplementedError
    

class TTLRUCache(TTCache):
    def __init__(self, capacity):
        # 缓存容量
        self._capacity = capacity
        # 缓存
        self._cache = TTOrderedDict()
    
    @property
    def capacity(self):
        return self._capacity
    
    @property
    def size(self):
        return len(self._cache)
    
    def front(self):
        assert(self.size > 0)
        return self._cache.frontitem()[1]
        
    def set(self, key, value):
        '''
        添加key, value到缓存
        '''
        exists = self._cache.get(key)
        if exists:
            self._cache[key] = (value, time.time())
        else:
            if len(self._cache) >= self._capacity:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time())
    
    def get(self, key):
        '''
        根据key获取value
        '''
        item = self._cache.pop(key, None)
        if item:
            self._cache[key] = (item[0], time.time())
            return item[0]
        return None

    def remove(self, key):
        '''
        删除
        '''
        item = self._cache.pop(key, None)
        if item:
            return item[0]
        return None


if __name__ == '__main__':
    cache = TTLRUCache(100)
    cache.set('key1', 1)
    cache.set('key2', 2)
    cache.get('key1')
    print(cache._cache.frontitem())


