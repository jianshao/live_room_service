# -*- coding=utf-8 -*-
'''
Created on 2017年12月18日

@author: zhaojiangang
'''
import functools
import importlib
import os

import tomato
from tomato.core.exceptions import TTException
from tomato.http.http import TTHttpUtils
from tomato.utils import ttlog


TT_DECOR_PARAMS_KEY = '__tt_deco_params__'
TT_DECOR_TYPE_MSG_HANDLER = 'msgHandler'
TT_DECOR_TYPE_REMOTE_METHOD = 'remoteMethod'
TT_DECOR_TYPE_HTTP_HANDLER = 'httpHandler'
TT_DECOR_TYPE_SYS_REMOTE_METHOD = 'sysRemoteMethod'


def messageHandler(route):
    def decorator_method(method):
        decorParams = {'type':TT_DECOR_TYPE_MSG_HANDLER}
        @functools.wraps(method)
        def wrapper(*args, **kw):
            return method(*args, **kw)
        decorParams['route'] = route
        decorParams['org'] = method
        setattr(wrapper, TT_DECOR_PARAMS_KEY, decorParams)
        return wrapper
    return decorator_method

def registerMessageHandler(app, serverType, decorParams, module, method):
    route = decorParams['route']
    app.routeController.setServerTypeByRoute(route, serverType)
    if app.serverType == serverType:
        ttlog.info('decorator.registerMessageHandler',
                   'route=', route,
                   'serverType=', serverType,
                   'decorParams=', decorParams,
                   'module=', module,
                   'method=', method)
        app.registerMessageHandler(route, method)


SERVER_SYS_TYPE_FRONTEND = 'frontend'
SERVER_SYS_TYPE_BACKEND = 'backend'
SERVER_SYS_TYPE_ALL = 'all'

SERVER_SYS_TYPES = [SERVER_SYS_TYPE_FRONTEND, SERVER_SYS_TYPE_BACKEND, SERVER_SYS_TYPE_ALL]

def _getServerFEType():
    if tomato.app.isFrontend():
        return SERVER_SYS_TYPE_FRONTEND
    return SERVER_SYS_TYPE_BACKEND

def isCallMe(decorParams):
    serverType = decorParams['serverType']
    return (serverType == SERVER_SYS_TYPE_ALL
            or tomato.app.serverType == serverType
            or serverType == _getServerFEType())
    
def remoteMethod(name=None):
    def decorator_method(method):
        decorParams = {'type':TT_DECOR_TYPE_REMOTE_METHOD}
        @functools.wraps(method)
        def wrapper(*args, **kw):
            if not isCallMe(decorParams):
                raise TTException(-1, 'Remote method only call in', decorParams['serverType'])
            return method(*args, **kw)
        methodName = name or method.__name__
        decorParams['methodName'] = methodName
        decorParams['org'] = method
        setattr(wrapper, TT_DECOR_PARAMS_KEY, decorParams)
        return wrapper
    return decorator_method
 
def registerRemoteMethod(app, serverType, decorParams, module, method):
    serviceName = getattr(module, '__serviceName__') if hasattr(module, '__serviceName__') else module.__name__
    decorParams['serverType'] = serverType
    decorParams['serviceName'] = serviceName
    methodName = decorParams['methodName']
    org = decorParams['org']
    if (serverType == SERVER_SYS_TYPE_ALL
        or app.serverType == serverType
        or serverType == _getServerFEType()):
        ttlog.info('decorator.registerRemoteMethod',
                   'serverType=', serverType,
                   'serviceName=', serviceName,
                   'methodName=', methodName,
                   'module=', module,
                   'method=', id(method),
                   'decorParams=', decorParams,
                   'org=', org)

        app.registerRemoteMethod(serviceName, org, methodName)

def httpHandler(path):
    def decorator_method(method):
        decorParams = {'type':TT_DECOR_TYPE_HTTP_HANDLER, 'path':path}
        @functools.wraps(method)
        def wrapper(*args, **kw):
            return method(*args, **kw)
        decorParams['org'] = method
        setattr(wrapper, TT_DECOR_PARAMS_KEY, decorParams)
        return wrapper
    return decorator_method

def httpJsonHandler(path):
    def decorator_method(method):
        decorParams = {'type':TT_DECOR_TYPE_HTTP_HANDLER, 'path':path}
        @functools.wraps(method)
        def wrapper(*args, **kw):
            resp = method(*args, **kw)
            if ttlog.isDebugEnabled():
                request = args[0]
                ttlog.debug('Http response',
                            'uri=', request.path,
                            'clientIp=', TTHttpUtils.getClientIp(request),
                            'args=', request.args,
                            'content=', request.content.getvalue(),
                            'resp=', resp)
            TTHttpUtils.finishResponseJson(args[0], resp, {'Access-Control-Allow-Origin':'*'})
        decorParams['org'] = method
        setattr(wrapper, TT_DECOR_PARAMS_KEY, decorParams)
        return wrapper
    return decorator_method

def registerHttpHandler(app, serverType, decorParams, module, method):
    if app.serverType == serverType:
        ttlog.info('decorator.registerHttpHandler',
                   'serverType=', serverType,
                   'decorParams=', decorParams,
                   'module=', module,
                   'method=', method)
        app.registerHttpHandler(decorParams['path'], method)

def listPackageModules(pkgName, recursion):
    '''
    列出pkgName包下所有模块
    '''
    pkgNames = [pkgName]
    while pkgNames:
        pkgName = pkgNames.pop(0)
        if ttlog.isDebugEnabled():
            ttlog.debug('decorator.listPackageModules',
                        'pkgName=', pkgName,
                        'recursion=', recursion)
        pkg = importlib.import_module(pkgName)
        moduleNames = set()
        for p in pkg.__path__:
            for fname in os.listdir(p):
                if os.path.isfile(os.path.join(p, fname)):
                    if (fname.endswith('.py') or fname.endswith('.pyc')) and fname.find('__init__') < 0:
                        moduleNames.add(pkgName + '.' + fname.rsplit('.', 1)[0])
                elif os.path.isdir(p):
                    pkgNames.append(pkgName + '.' + fname)
        for moduleName in moduleNames:
            yield moduleName

def listSubPackages(pkgName):
    try:
        pkg = importlib.import_module(pkgName)
        for p in pkg.__path__:
            for fname in os.listdir(p):
                if os.path.isdir(os.path.join(p, fname)):
                    yield fname, pkgName + '.' + fname
    except:
        pass

def listDecoratorModuleMethod(pkgName, recursion):
    for moduleName in listPackageModules(pkgName, recursion):
        module = importlib.import_module(moduleName)
        for k in dir(module):
            v = getattr(module, k)
            if callable(v) and hasattr(v, TT_DECOR_PARAMS_KEY) and moduleName == v.__module__:
                yield (module, k, v)

def loadSystemRemote(app, pkgName, recursion=True):
    for serverType in SERVER_SYS_TYPES:
        for module, _mname, method in listDecoratorModuleMethod(pkgName + '.' + serverType, recursion):
            decorParams = getattr(method, TT_DECOR_PARAMS_KEY)
            decorType = decorParams.get('type')
            if decorType == TT_DECOR_TYPE_REMOTE_METHOD:
                registerRemoteMethod(app, serverType, decorParams, module, method)

def loadServerPackage(app, serverType, pkgName, recursion):
    for module, _mname, method in listDecoratorModuleMethod(pkgName, recursion):
        decorParams = getattr(method, TT_DECOR_PARAMS_KEY)
        decorType = decorParams.get('type')
        if decorType == TT_DECOR_TYPE_MSG_HANDLER:
            registerMessageHandler(app, serverType, decorParams, module, method)
        elif decorType == TT_DECOR_TYPE_REMOTE_METHOD:
            registerRemoteMethod(app, serverType, decorParams, module, method)
        elif decorType == TT_DECOR_TYPE_HTTP_HANDLER:
            registerHttpHandler(app, serverType, decorParams, module, method)
        else:
            ttlog.error('loadServerPackageDecorator UnknownDecoratorType', serverType, pkgName, decorType)

def loadServerPackageDecorator(app, pkgName, recursion=True):
    for serverType, subPkgName in listSubPackages(pkgName):
        loadServerPackage(app, serverType, subPkgName, recursion)


