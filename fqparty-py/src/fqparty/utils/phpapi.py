# -*- coding:utf-8 -*-
'''
Created on 2021年1月22日

@author: zhaojiangang
'''

from tomato.config import configure
from tomato.http.http import TTHttpClient
from tomato.utils import ttlog, strutil


def notifyHeartbeat(userId):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')

    if not url:
        ttlog.warn('phpapi.notifyHeartbeat',
                   'userId=', userId,
                   'err=', 'NoPhpServerUrlConf')
        return

    url += '/api/inner/heartbeat'
    url = str(url)

    params = {
        'uid': userId,
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.notifyHeartbeat',
                    'userId=', userId,
                    'url=', url)
    TTHttpClient.postForm(url, params, block=False)

def notifyRoomOnline(userId, roomId, duration):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')
    
    if not url:
        ttlog.warn('phpapi.notifyRoomOnline',
                   'userId=', userId,
                   'roomId=', roomId,
                   'duration=', duration,
                   'err=', 'NoPhpServerUrlConf')
        return
    
    url += '/api/v1/userRoomOnline'
    url = str(url)
    
    params = {
        'uid': userId,
        'roomid': roomId,
        'duration': duration
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.notifyRoomOnline',
                    'userId=', userId,
                    'roomId=', roomId,
                    'duration=', duration,
                    'url=', url)
    TTHttpClient.postForm(url, params, block=False)

def queryUserInfoForRoom(userId):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')
    
    if not url:
        ttlog.warn('phpapi.queryUserInfoForRoom',
                   'userId=', userId,
                   'err=', 'NoPhpServerUrlConf')
        return
    
    url += '/api/inner/queryUserInfoForRoom'
    url = str(url)
    
    params = {
        'userId': userId,
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.queryUserInfoForRoom',
                    'userId=', userId,
                    'url=', url)
    resp = TTHttpClient.get(url, params=params, timeout=5)
    respJson = strutil.jsonLoads(resp)
    code = respJson.get('code', 0)
    if code != 200:
        return code, respJson.get('desc', '')
    
    return 0, respJson.get('data')


def queryRoomInfoForRoom(roomId):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')

    if not url:
        ttlog.warn('phpapi.queryRoomInfoForRoom',
                   'roomId=', roomId,
                   'err=', 'NoPhpServerUrlConf')
        return

    url += '/api/inner/queryRoomInfoForRoom'
    url = str(url)

    params = {
        'roomId': roomId,
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.queryRoomInfoForRoom',
                    'roomId=', roomId,
                    'url=', url)
    resp = TTHttpClient.get(url, params=params, timeout=5)
    respJson = strutil.jsonLoads(resp)
    code = respJson.get('code', 0)
    if code != 200:
        return code, respJson.get('desc', '')

    return 0, respJson.get('data')


def searchRoomInfoForRoom(searchId):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')

    if not url:
        ttlog.warn('phpapi.searchRoomInfoForRoom',
                   'searchId=', searchId,
                   'err=', 'NoPhpServerUrlConf')
        return

    url += '/api/inner/searchRoomInfoForRoom'
    url = str(url)

    params = {
        'searchId': searchId,
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.searchRoomInfoForRoom',
                    'searchId=', searchId,
                    'url=', url)
    resp = TTHttpClient.get(url, params=params, timeout=5)
    respJson = strutil.jsonLoads(resp)
    code = respJson.get('code', 0)
    if code != 200:
        return code, respJson.get('desc', '')

    return 0, respJson.get('data')


def queryAttentionForRoom(userId, userIdEd):
    url = configure.loadJson('server.fqparty.global', {}).get('phpServerUrl', '')

    if not url:
        ttlog.warn('phpapi.queryAttentionForRoom',
                   'userId=', userId,
                   'userIdEd=', userIdEd,
                   'err=', 'NoPhpServerUrlConf')
        return

    url += '/api/inner/queryAttentionForRoom'
    url = str(url)

    params = {
        'userId': userId,
        'userIdEd': userIdEd,
    }

    if ttlog.isDebugEnabled():
        ttlog.debug('phpapi.queryAttentionForRoom',
                    'userId=', userId,
                   'userIdEd=', userIdEd,
                    'url=', url)
    resp = TTHttpClient.get(url, params=params, timeout=5)
    respJson = strutil.jsonLoads(resp)
    code = respJson.get('code', 0)
    if code != 200:
        return code, respJson.get('desc', '')

    return 0, respJson.get('data')

