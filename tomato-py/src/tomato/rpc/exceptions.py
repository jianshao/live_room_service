# -*- coding:utf-8 -*-
'''
Created on 2017年5月16日

@author: zhaojiangang
'''
from tomato.core.exceptions import TTException


class TTRPCException(TTException):
    def __init__(self, ec, message):
        super(TTRPCException, self).__init__(ec, message)


class TTRPCChannelAlreayClosedException(TTRPCException):
    pass


class TTRPCChannelException(TTRPCException):
    pass


class TTRPCNoSuchChannelException(TTRPCChannelException):
    pass


class TTRPCPenddingException(TTRPCException):
    pass


class TTRPCNoSuchServiceException(TTRPCException):
    def __init__(self, message='No such service'):
        super(TTRPCNoSuchServiceException, self).__init__(-1, message)


class TTRPCNoSuchMethodException(TTRPCException):
    def __init__(self, message='No such method'):
        super(TTRPCNoSuchMethodException, self).__init__(-1, message)


class TTRPCRemoteException(TTRPCException):
    def __init__(self, ec, message):
        super(TTRPCRemoteException, self).__init__(ec, message)

