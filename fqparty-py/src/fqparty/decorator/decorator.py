# -*- coding=utf-8 -*-
'''
Created on 2018年5月3日

@author: zhaojiangang
'''
import functools
from tomato.core.exceptions import TTException
from tomato.utils import ttlog, strutil
from tomato.common.proxy import session_remote_proxy
from fqparty.utils import time_utils


def exceptionHandler(method):
    @functools.wraps(method)
    def wrapper(*args, **kw):
        try:
            return method(*args, **kw)
        except TTException, e:
            return {'ec':e.errorCode, 'info':e.message}
        except Exception, e:
            ttlog.error()
            return {'ec':-1, 'info':e.message}
    return wrapper


def exceptionHandlerOld(method):
    @functools.wraps(method)
    def wrapper(*args, **kw):
        try:
            return method(*args, **kw)
        except TTException, e:
            return {'code':e.errorCode, 'desc':e.message, 'data':None}
        except Exception, e:
            ttlog.error()
            return {'code':-1, 'desc':e.message, 'data':None}
    return wrapper


def exceptionRoomHandlerOld(method):
    @functools.wraps(method)
    def wrapper(*args, **kw):
        startTime = time_utils.getCurrentTimestampFloat()
        msg = args[0]
        sessionInfo = args[1]
        roomId = msg.body.get('roomId')
        msgId = msg.body.get('msgId')

        try:
            return method(*args, **kw)
        except TTException, e:
            msgdata = {'msgId': msgId, 'code': e.errorCode, 'roomId': roomId, 'desc': e.message}
            session_remote_proxy.pushRawData(strutil.jsonDumps(msgdata), sessionInfo.frontId, sessionInfo.userId)

            return {'code': e.errorCode, 'desc': e.message, 'data': None}
        except Exception, e:
            ttlog.error()
            msgdata = {'msgId': msgId, 'code': -1, 'roomId': roomId, 'desc': "服务器异常"}
            session_remote_proxy.pushRawData(strutil.jsonDumps(msgdata), sessionInfo.frontId, sessionInfo.userId)
            return {'code': -1, 'desc': e.message, 'data': None}
        finally:
            endTime = time_utils.getCurrentTimestampFloat()
            if endTime - startTime >= 1:
                ttlog.info('exceptionRoomHandlerOld methodName =', method.__name__,
                           'endTime=', endTime,
                           'startTime=', startTime,
                           'diff=', endTime - startTime,
                           'args=', msg.body)

    return wrapper

def remoteExceptionHandler(method):
    @functools.wraps(method)
    def wrapper(*args, **kw):
        startTime = time_utils.getCurrentTimestampFloat()
        try:
            res = method(*args, **kw)
            return 0, res
        except TTException, e:
            return e.errorCode, e.message
        except Exception, e:
            ttlog.error()
            return -1, e.message
        finally:
            endTime = time_utils.getCurrentTimestampFloat()
            if endTime - startTime >= 1:
                ttlog.info('remoteExceptionHandler methodName =',  method.__name__,
                           'endTime=', endTime,
                           'startTime=', startTime,
                           'diff=', endTime-startTime,
                           'args=', args)
    return wrapper


