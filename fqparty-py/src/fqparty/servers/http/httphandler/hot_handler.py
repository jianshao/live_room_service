# -*- coding:utf-8 -*-
'''
Created on 2020年11月3日

@author: zhaojiangang
'''
from fqparty.const import HttpResponseCode, ErrorCode
from fqparty.decorator.decorator import exceptionHandlerOld
from fqparty.utils import http_util

from tomato.common.proxy import hotfix_remote_proxy
from tomato.http.http import TTHttpUtils
from tomato.core.exceptions import TTException
from tomato.decorator.decorator import httpJsonHandler


@httpJsonHandler(path='/iapi/reloadConfig')
@exceptionHandlerOld
def reloadConfig(request):
    try:
        serverIds = TTHttpUtils.getParamString(request, 'serverIds')
        hotfix_remote_proxy.reloadConfig(serverIds)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)
