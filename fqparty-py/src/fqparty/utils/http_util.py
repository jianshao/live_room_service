# -*- coding:utf-8 -*-
'''
Created on 2020年11月2日

@author: zhaojiangang
'''
from sre_compile import isstring

import fqparty
from fqparty.const import ErrorCode
from tomato.core.exceptions import TTException
from tomato.http.http import TTHttpUtils
from tomato.utils import ttlog, strutil


class HttpJsonForm(object):
    def __init__(self, request):
        self.msg = strutil.jsonLoads(request.content.getvalue())
    
    def getParamDict(self, name):
        if not self.msg.has_key(name):
            raise ValueError()
        v = self.msg.get(name)
        if not isinstance(v, dict):
            raise ValueError()
        return v

    def getIntParam(self, name):
        if not self.msg.has_key(name):
            raise ValueError()
        v = self.msg.get(name)
        if not isinstance(v, int):
            raise ValueError()
        return v

    def getIntParamDefault(self, name, default=None):
        v = self.msg.get(name, default)
        if not isinstance(v, int):
            raise ValueError()
        return v
    
    def getIntOptionParam(self, name, defVal=0):
        if not self.msg.has_key(name):
            return defVal
        v = self.msg.get(name)
        if not isinstance(v, int):
            raise ValueError()
        return v
    
    def getStringParam(self, name):
        if not self.msg.has_key(name):
            raise ValueError()
        v = self.msg.get(name)
        if not isstring(v):
            raise ValueError()
        return v
    
    def getStringOptionParam(self, name, defVal=''):
        if not self.msg.has_key(name):
            return defVal
        v = self.msg.get(name)
        if not isstring(v):
            raise ValueError()
        return v


def authToken(request):
    token = TTHttpUtils.getHeader(request, 'token')
    if not token:
        ttlog.info('authToken NoToken',
                        'request=', request.path,
                        'token=', token)
        raise TTException(ErrorCode.AUTH_TOKEN_FAILED)
    
    userId = fqparty.app.utilService.getUserIdByToken(token)
    if userId <= 0:
        ttlog.info('authToken NotFoundUserIdByToken',
                        'request=', request.path,
                        'token=', token)
        raise TTException(ErrorCode.AUTH_TOKEN_FAILED)
    
    return userId, token


def makeResponseOld(code, info, data, params=None):
    ret = {
        'code':code,
        'desc':info,
        'data':data
    }
    if params:
        ret.update(params)
    return ret


