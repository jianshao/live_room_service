# -*- coding:utf-8 -*-
'''
Created on 2017年11月7日

@author: zhaojiangang
'''
import json
import re
import urllib
import urlparse

from twisted.web import http, client

from tomato.core import reactor
from tomato.core.exceptions import TTException
from tomato.core.future import TTFuture
from tomato.core.tasklet import TTTasklet
from tomato.utils import ttlog, strutil
from tomato.utils.fileutils import TTFileUtils


class HttpException(TTException):
    pass


class HttpNotFoundException(HttpException):
    def __init__(self, message='404 Not found'):
        super(HttpNotFoundException, self).__init__(-1, message)


class HttpServerInternalException(HttpException):
    def __init__(self, message='500 Server error'):
        super(HttpServerInternalException, self).__init__(-1, message)


class HttpRequestFactory(http.Request):
    def process(self):
        self.channel.factory.handleRequest(self)


def defaultHttpErrorHandler(request, e):
    if isinstance(e, HttpNotFoundException):
        request.setResponseCode(404)
    else:
        request.setResponseCode(500)
    request.finish()


class TTHttpRequestController(object):
    '''http请求控制器'''
    def __init__(self):
        self._handlers = []
        # map<path, handler>
        self._handlerMap = {}
        # 错误处理器
        self._errorHandler = defaultHttpErrorHandler

    def handleRequest(self, server, request):
        try:
            if ttlog.isDebugEnabled():
                ttlog.debug('TTHttpRequestController.handleRequest',
                            'uri=', request.path,
                            'clientIp=', TTHttpUtils.getClientIp(request),
                            'args=', request.args,
                            'content=', request.content.getvalue(),
                            'token=', request.getHeader('token'))
            handler = self.findHandler(request.path)
            if handler:
                handler(request)
            else:
                raise HttpNotFoundException('Not found handler for request %s %s' % (request.path, TTHttpUtils.getClientIp(request)))
        except Exception, e:
            ttlog.warn('Error handle request',
                       'uri=', request.path,
                       'clientIp=', TTHttpUtils.getClientIp(request),
                       'args=', request.args,
                       'content=', request.content.getvalue())
            self._errorHandler(request, e)

    def addHandler(self, path, handler):
        '''添加handler'''
        if path in self._handlerMap:
            raise TTException(-1, 'path already exists: %s %s' % (path, handler))
        r = re.compile(path)
        self._handlers.append((r, path, handler))
        self._handlerMap[path] = handler

    def findHandler(self, path):
        '''根据path查找handler'''
        handler = self._handlerMap.get(path)
        if handler:
            return handler

        for handler in self._handlers:
            if handler[0].match(path):
                return handler[2]

        return None

    def setErrorHandler(self, handler):
        self._errorHandler = handler


DEFAULT_MIMETYPES = {
            'txt':'text/plain;charset=utf8',
            'html':'text/html;charset=utf8',
            'css':'text/css;charset=utf8',
            'js':'application/x-javascript;charset=utf8',
            'png':'image/png',
            'jpeg':'image/jpeg',
            'jpg':'image/jpeg',
        }


class TTHttpFileResource(object):
    def __init__(self, rootpath, fileMimitypes=None):
        self._rootpath = rootpath
        self._fileMimetypes = fileMimitypes or DEFAULT_MIMETYPES

    def handleRequest(self, app, request):
        mimetypes = self._getMimetypes(request.path)
        headers = {'Content-Type':mimetypes}
        app.finishResponseFile(request, self._rootpath + request.path , headers)

    def _getMimetypes(self, path):
        suffix = TTFileUtils.getFileSuffix(path).lower()
        mimetype = self._fileMimetypes.get(suffix)
        if not mimetype:
            mimetype = 'application/octet-stream'
        return mimetype


class TTHttpUtils(object):
    JSON_HEADERS = {'Content-Type':'application/json;charset=utf8'}

    @classmethod
    def getHeader(cls, request, name):
        return request.getHeader(name)

    @classmethod
    def getParamsDict(cls, request):
        ret = {}
        for k, v in request.args.iteritems():
            if v:
                ret[k] = v[0]
        return ret

    @classmethod
    def getClientIp(cls, request):
        ip = request.getHeader('x-forwarded-for')
        if ip:
            ips = ip.split(',')
            if len(ips) > 1 :
                ip = ips[-2]
            else:
                ip = ips[-1]
            ip = ip.strip()
        else:
            ip = request.getHeader('x-real-ip')
            if not ip:
                ip = request.getClientIP()
        return ip

    @classmethod
    def getParamString(cls, request, name):
        paramList = request.args.get(name)
        if paramList:
            return paramList[0]
        raise TypeError('Not found param ' + str(name))

    @classmethod
    def getParamStringDefault(cls, request, name, defaultValue=None):
        paramList = request.args.get(name)
        if paramList:
            return paramList[0]
        return defaultValue

    @classmethod
    def getParamInt(cls, request, name):
        value = cls.getParamString(request, name)
        return int(value)

    @classmethod
    def getParamIntDefault(cls, request, name, defaultValue=0):
        value = cls.getParamStringDefault(request, name, None)
        if value is None:
            return defaultValue
        return int(value)

    @classmethod
    def getParamStringArray(cls, request, name, sep=',', removeEmpty=True, defaultValue=None):
        svalue = cls.getParamString(request, name)
        if svalue:
            arr = svalue.split(sep)
            if removeEmpty:
                for i in range(len(arr) - 1, -1, -1):
                    if len(arr[i]) == 0:
                        del arr[i]
            return arr
        return defaultValue

    @classmethod
    def getParamIntArray(cls, request, name, sep=',', removeEmpty=True, defaultValue=None):
        sarr = cls.getParamStringArray(request, name, sep, removeEmpty, defaultValue)
        if sarr:
            return [int(istr) for istr in sarr]
        return sarr

    @classmethod
    def getParamJson(cls, request, name, defaultValue=None, checkType=None):
        paramList = request.args.get(name)
        if paramList:
            jsonstr = paramList[0]
            return json.loads(jsonstr, encoding='utf8')
        return defaultValue

    @classmethod
    def finishResponseJson(cls, request, response, headers=None, statusCode=200):
        response = strutil.jsonDumps(response)
        headers = headers or {}
        headers.update(cls.JSON_HEADERS)
        return cls.finishResponse(request, response, headers, statusCode)

    @classmethod
    def finishResponse(cls, request, response, headers=None, statusCode=200):
        try:
            if headers:
                for k, v in headers.items():
                    request.setHeader(k, v)
            if response:
                if isinstance(response, unicode):
                    response = response.encode('utf8')
                request.write(response)
            if not statusCode is None:
                request.setResponseCode(statusCode)
        finally:
            request.finish()

    @classmethod
    def finishResponseFile(cls, request, path, headers=None, statusCode=200):
        f = None
        try:
            if headers:
                for k, v in headers.items():
                    request.setHeader(k, v)
            f = open(path, 'rb')
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                request.write(chunk)
            request.setResponseCode(statusCode)
        except:
            request.setResponseCode(404)
        finally:
            if f:
                try:
                    f.close()
                except:
                    pass
            request.finish()


class TTHttpServer(http.HTTPFactory):
    '''http服务器'''
    def __init__(self, httpController, conf, *args, **kw):
        http.HTTPFactory.__init__(self, *args, **kw)
        self.conf = conf
        self.listening = None
        self.httpController = httpController or TTHttpRequestController()

    def start(self):
        if not self.listening:
            host = self.conf.get('host', '0.0.0.0')
            self.listening = reactor.listenTCP(self.conf['port'], self, self.conf.get('backlog', 500), host)
            ttlog.info('TTHttpServer.start',
                       'host=', host,
                       'port=', self.conf.get('port'))

    def stop(self):
        if self.listening:
            self.listening.stopListening()
            self.listening = None

    def buildProtocol(self, addr):
        channel = http.HTTPFactory.buildProtocol(self, addr)
        channel.factory = self
        channel.requestFactory = HttpRequestFactory
        return channel

    def handleRequest(self, request):
        TTTasklet.createTasklet(self.httpController.handleRequest, self, request)


class TTHttpClient(object):
    @classmethod
    def get(cls, url, headers=None, params=None, timeout=0, block=True):
        return cls._getPage(url, 'GET', headers=headers, params=params, timeout=timeout, block=block)

    @classmethod
    def getJson(cls, url, headers=None, params=None, timeout=0, block=True):
        jstr = cls._getPage(url, 'GET', headers=headers, params=params, timeout=timeout, block=block)
        return strutil.jsonLoads(jstr)

    @classmethod
    def postForm(cls, url, params=None, headers=None, encoding=None, timeout=0, block=True):
        encoding = encoding or 'utf8'
        contentType = 'application/x-www-form-urlencoded;charset=' + str(encoding)
        data = cls._encodeParams(params, encoding)
        return cls.postData(url, data, headers=headers, contentType=contentType, timeout=timeout, block=block)

    @classmethod
    def postData(cls, url, data, headers=None, contentType=None, timeout=0, block=True):
        headers = headers or {}
        contentType = contentType or 'application/octet-stream'
        headers['Content-Type'] = contentType
        return cls._getPage(url, 'POST', headers=headers, params=None, data=data, timeout=timeout, block=block)

    @classmethod
    def _getPage(cls, url, method, headers=None, params=None, data=None, timeout=0, block=True):
        if params:
            parsedUrl = urlparse.urlparse(url)
            qparams = urlparse.parse_qs(parsedUrl.query) if parsedUrl.query else {}
            qparams.update(params)
            newUrl = urlparse.urlunparse((parsedUrl[0], parsedUrl[1], parsedUrl[2], parsedUrl[3], urllib.urlencode(qparams), parsedUrl[5]))
            url = newUrl
        d = client.getPage(url, method=method, headers=headers, postdata=data, timeout=timeout)
        ret = TTFuture(d)
        if block:
            return ret.get(timeout if timeout else None)
        return ret

    @classmethod
    def _ensureStr(cls, string, encoding='utf8'):
        if isinstance(string, unicode):
            return string.encode(encoding)
        if isinstance(string, str):
            if encoding and 'utf8' != encoding:
                return string.decode('utf8').encode(encoding)
            return string
        return str(string)

    @classmethod
    def _encodeParams(cls, params, encoding='utf8'):
        l = []
        if params:
            for k, v in params.items():
                k = urllib.quote_plus(cls._ensureStr(k, encoding))
                v = urllib.quote_plus(cls._ensureStr(v, encoding))
                l.append(k + '=' + v)
        return '&'.join(l)


if __name__ == '__main__':
    resp = TTHttpClient.get('https://testgosocket.fqparty.com/ws')
    print(resp)


