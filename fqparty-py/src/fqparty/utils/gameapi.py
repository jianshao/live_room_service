# -*- coding:utf-8 -*-
'''
Created on 2021年1月22日

@author: zhaojiangang
'''
from datetime import datetime

from fqparty.utils import proto_utils
from tomato.config import configure
from tomato.http.http import TTHttpClient
from tomato.utils import ttlog, timeutil, strutil


def gameStart(roomId, userId, gameId, mics):
    gameServerUrl = configure.loadJson('server.fqparty.global', {}).get('gameServerUrl', '')
    if not gameServerUrl:
        ttlog.warn('gameapi.gameStart',
                   'roomId=', roomId,
                   'userId=', userId,
                   'gameId=', gameId,
                   'mics=', [(mic.micId, mic.roomUser.userId if mic.roomUser else 0)
                             for mic in mics],
                   'err=', 'NoGameServerUrlConf')
        return
    
    gameServerUrl += '/inner/v1/game_start'
    gameServerUrl = str(gameServerUrl)
    micInfos = {}
    timestamp = timeutil.currentTimestamp()
    for mic in mics:
        countdownTime = '' if (mic.countdownTime == 0 or mic.countdownTime >= timestamp) else datetime.fromtimestamp(mic.countdownTime).strftime('%Y-%m-%dT%H:%M:%S.0+08:00')
        micInfos[mic.micId] = {
            'micId':mic.micId,
            'isLocked':mic.locked,
            'isDisabled':mic.disabled,
            'countdownTime':countdownTime,
            'inviteUserId':mic.inviteUserId,
            'inviteRoomId':mic.inviteRoomId,
            'xinDongZhi':mic.heartValue,
            'user':proto_utils.encodeUser(mic.roomUser.user) if mic.roomUser else None,
            'emoticonAnimationUrl':proto_utils.buildImageUrl(mic.emoticon.animation) if mic.emoticon else ''
        }
    params = {
        'roomId': roomId,
        'userId': userId,
        'pluginId': gameId,
        'microInfos': micInfos
    }
    
    if ttlog.isDebugEnabled():
        ttlog.info('gameapi.gameStart',
                   'gameServerUrl=', gameServerUrl,
                   'roomId=', roomId,
                   'userId=', userId,
                   'gameId=', gameId,
                   'mics=', [(mic.micId, mic.roomUser.userId if mic.roomUser else 0)
                             for mic in mics],)

    data = strutil.jsonDumps(params)
    resp = TTHttpClient.postForm(gameServerUrl, {'data':data}, timeout=10, block=True)
    ttlog.info('gameapi.gameStart',
               'gameServerUrl=', gameServerUrl,
               'roomId=', roomId,
               'userId=', userId,
               'gameId=', gameId,
               'mics=', [(mic.micId, mic.roomUser.userId if mic.roomUser else 0)
                             for mic in mics],
               'resp=', resp)
    return resp
    
def gameLeave(roomId, userId, gameId, micId):
    gameServerUrl = configure.loadJson('server.fqparty.global', {}).get('gameServerUrl', '')
    if not gameServerUrl:
        ttlog.warn('gameapi.gameLeave',
                   'roomId=', roomId,
                   'userId=', userId,
                   'gameId=', gameId,
                   'micId=', micId,
                   'err=', 'NoGameServerUrlConf')
        return
    
    gameServerUrl += '/inner/v1/leave'
    gameServerUrl = str(gameServerUrl)
    
    params = {
        'roomId':roomId,
        'userId':userId,
        'seatId':micId,
        'pluginId':gameId
    }
    resp = TTHttpClient.postForm(gameServerUrl, params, timeout=10, block=True)
    ttlog.info('gameapi.gameLeave',
               'gameServerUrl=', gameServerUrl,
               'roomId=', roomId,
               'userId=', userId,
               'gameId=', gameId,
               'micId=', micId,
               'resp=', resp)
    return resp

    
