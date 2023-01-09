# -*- coding=utf-8 -*-
'''
Created on 2016年12月25日

@author: zjgzzz@126.com
'''


class TTException(Exception):
    def __init__(self, ec=-1, message=''):
        super(TTException, self).__init__(ec, message)
    
    @property
    def errorCode(self):
        return self.args[0]
    
    @property
    def message(self):
        return self.args[1]


class TTTimeoutException(TTException):
    def __init__(self, message='Timeout exception'):
        super(TTTimeoutException, self).__init__(-1, message)


