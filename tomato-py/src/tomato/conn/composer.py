# -*- coding=utf-8 -*-
'''
Created on 2017年11月22日

@author: zhaojiangang
'''
import struct

from tomato.core.exceptions import TTException
from tomato.utils import ttlog


class TTComposer(object):
    def feed(self, data):
        '''
        增加data
        @return: iterator<解包后的数据>
        '''
        raise NotImplementedError
    
    def compose(self, data):
        '''
        打包
        @return: 打包后的数据
        '''
        raise NotImplementedError


class TTComposerFake(object):
    def feed(self, data):
        '''
        增加data
        @return: iterator<解包后的数据>
        '''
        yield data
    
    def compose(self, data):
        '''
        打包
        @return: 打包后的数据
        '''
        return data


class TTComposerInt32String(TTComposer):
    headFmt = '!I'
    headLen = struct.calcsize(headFmt)
    maxLen = 65535
    
    def __init__(self):
        self._buf = b''

    def feed(self, data):
        self._buf += data
    
        while len(self._buf) > self.headLen:
            length, = struct.unpack(self.headFmt, self._buf[0:self.headLen])
            if length > self.maxLen:
                raise TTException(-1, 'Too long string %s %s' % (length, self.maxLen))
            
            pstart = self.headLen
            pend = self.headLen + length
            if len(self._buf) < pend:
                break
            else:
                pkg = self._buf[pstart:pend]
                self._buf = self._buf[pend:]
                yield pkg
        
    def compose(self, data):
        if len(data) > self.maxLen:
            raise TTException(-1, 'Too long string %s %s' % (len(data), self.maxLen))
        return struct.pack(self.headFmt, len(data)) + data


if __name__ == '__main__':
    composer = TTComposerInt32String()
    data = 'data1'
    edata = composer.compose(data)
    ttlog.info(edata)
    


