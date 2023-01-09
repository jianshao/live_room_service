# -*- coding=utf-8 -*-
'''
Created on 2018年1月22日

@author: zhaojiangang
'''
from tomato.decorator.decorator import httpJsonHandler
from tomato.http.http import TTHttpUtils



@httpJsonHandler(path='/test/v1/sayHello')
def testUtilLogin(request):
    userId = TTHttpUtils.getParamIntDefault(request, 'userId', 0)
    return {'userId':userId}

@httpJsonHandler(path='/test/v1/hotfix')
def testHotfix(request):
    pypath = TTHttpUtils.getParamStringDefault(request, 'pypath', 0)
    params = TTHttpUtils.getParamJson(request, 'params', {})
    return {'pypath':pypath, 'params':params}

@httpJsonHandler(path='/test/json')
def testJson(request):
    key = TTHttpUtils.getParamString(request, 'key')
    value = TTHttpUtils.getParamString(request, 'value')
    return {'key':key, 'value':value}


