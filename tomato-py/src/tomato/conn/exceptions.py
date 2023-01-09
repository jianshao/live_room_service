# -*- coding=utf-8 -*-
'''
Created on 2016年12月21日

@author: zjgzzz@126.com
'''
from tomato.core.exceptions import TTException


class TTMessageException(TTException):
    pass


class TTProtocolException(TTException):
    def __init__(self, message=''):
        super(TTProtocolException, self).__init__(-1, message)


class TTConnException(TTException):
    pass


