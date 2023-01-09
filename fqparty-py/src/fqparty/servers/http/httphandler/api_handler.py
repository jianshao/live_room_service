# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from sre_compile import isstring

import fqparty
from fqparty.const import HttpResponseCode, UserLeaveMicReason, ErrorCode, \
    UserLeaveRoomReason, MsgTypes
from fqparty.decorator.decorator import exceptionHandlerOld
from fqparty.proxy.mic import mic_remote_proxy
from fqparty.proxy.room import room_remote_proxy
from fqparty.proxy.user import user_remote_proxy
from fqparty.utils import http_util
from fqparty.utils.http_util import authToken, HttpJsonForm
from tomato.core.exceptions import TTException
from tomato.decorator.decorator import httpJsonHandler
from tomato.utils import strutil


@httpJsonHandler(path='/user/gameStart')
@exceptionHandlerOld
def userGameStart(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        gameId = form.getIntParam('pluginId')
        # ec, res = room_remote_proxy.gameStart(roomId, userId, gameId)
        # if ec != 0:
        #     return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'gameStart ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/onMic')
@exceptionHandlerOld
def userOnMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        micId = form.getIntParam('micId')
        ec, res = room_remote_proxy.userOnMic(roomId, userId, micId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'onMic ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/leaveMic')
@exceptionHandlerOld
def userLeaveMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        ec, res = room_remote_proxy.userLeaveMic(roomId, userId, UserLeaveMicReason.USER_ACTIVE)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'leaveMic ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/checkAuth')
@exceptionHandlerOld
def userCheckAuth(request):
    try:
        userId, _token = authToken(request)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'auth success', {'userId':userId, 'userName':''})
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/checkMic')
@exceptionHandlerOld
def userCheckMic(request):
    try:
        userId, _token = authToken(request)
        ec, res = user_remote_proxy.getUserRoomLocation(userId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        
        roomId = res['roomId']
        ec, res = room_remote_proxy.getUserMic(roomId, userId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        micId = res
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, '', {'roomId':roomId, 'micId':micId})
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/lockMic')
@exceptionHandlerOld
def userLockMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        micId = form.getIntParam('micId')
        locked = form.getIntParam('lock')
        # locked == 1 锁麦 locked == 2取消锁麦
        ec, res = mic_remote_proxy.lockMic(roomId, userId, micId, locked == 1)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/banMic')
@exceptionHandlerOld
def userBanMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        micId = form.getIntParam('micId')
        ban = form.getIntParam('ban')
        # ban == 1 禁麦， ban == 2取消禁麦
        ec, res = mic_remote_proxy.disableMic(roomId, userId, micId, ban == 1)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/getRoomUserInfo')
@exceptionHandlerOld
def getRoomUserInfo(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        queryUserId = form.getIntParam('userId')
        ec, res = room_remote_proxy.getRoomUserInfo(roomId, userId, queryUserId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/inviteMic')
@exceptionHandlerOld
def userInviteMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        micId = form.getIntParam('micId')
        inviteUserId = form.getIntParam('userId')
        cancel = form.getIntParam('cancel') == 2
        ec, res = mic_remote_proxy.inviteMic(roomId, userId, inviteUserId, micId, cancel)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', '')
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/countdownMic')
@exceptionHandlerOld
def userCountdownMic(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        micId = form.getIntParam('micId')
        cancel = form.getIntParam('cancel')
        # 1 设置 2 取消
        if cancel == 2:
            ec, res = mic_remote_proxy.cancelCountdownMic(roomId, userId, micId)
        else:
            duration = form.getIntParam('duration')
            ec, res = mic_remote_proxy.countdownMic(roomId, userId, micId, duration)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', '')
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/banRoomMsg')
@exceptionHandlerOld
def disableRoomMsg(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        disabled = form.getIntParam('disable')
        ec, res = mic_remote_proxy.disableRoomMsg(roomId, userId, disabled == 1)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', '')
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/syncMusicData')
@exceptionHandlerOld
def userSyncMusicData(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        msgstr = form.getStringParam('msg')
        msg = strutil.jsonLoads(msgstr)
        ec, res = room_remote_proxy.syncMusicData(roomId, userId, msg)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

def filterText(msgstr):
    msg = strutil.jsonLoads(msgstr)
    contentType = msg.get('messageType')
    if contentType == 0:
        content = msg.get('content')
        if content:
            text = content.get('text')
            if isstring(text):
                content['text'] = fqparty.app.keywordService.filter(text)
        msgstr = strutil.jsonDumps(msg)
    return msgstr

@httpJsonHandler(path='/push/pushRoom')
@exceptionHandlerOld
def pushRoom(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        msgType = form.getIntParam('msgType')
        msg = form.getStringParam('msg')
        if msgType == MsgTypes.TEXT:
            msg = filterText(msg)
        ec, res = room_remote_proxy.sendMsgToRoom(roomId, userId, msgType, msg)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/push/getRoomInfo')
@exceptionHandlerOld
def getRoomInfo(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        ec, res = room_remote_proxy.pushRoomInfo(roomId, userId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/push/getRoomUserList')
@exceptionHandlerOld
def getRoomUserList(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        listType = form.getIntParam('type')
        ec, res = room_remote_proxy.getRoomUserList(roomId, userId, listType)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/push/getRoomUserListAll')
@exceptionHandlerOld
def getRoomUserListAll(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        pageIndex = form.getIntParamDefault('pageIndex', 0)
        pageNum = form.getIntParamDefault('pageNum', 20)
        ec, res = room_remote_proxy.getRoomUserListAll(roomId, userId, pageIndex, pageNum)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/push/getRoomUserListThree')
@exceptionHandlerOld
def getRoomUserListThree(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        num = form.getIntParamDefault('num', 3)
        ec, res = room_remote_proxy.getRoomUserListThree(roomId, userId, num)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/room/searchRoom')
@exceptionHandlerOld
def searchRoom(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        searchId = form.getIntParam('searchId')
        ec, res = mic_remote_proxy.searchRoom(roomId, userId, searchId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok!', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/checkRoom')
@exceptionHandlerOld
def userCheckRoom(request):
    try:
        userId, _token = authToken(request)
        ec, res = user_remote_proxy.getUserRoomLocation(userId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, '', res)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/user/leaveRoom')
@exceptionHandlerOld
def userLeaveRoom(request):
    try:
        userId, _token = authToken(request)
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        ec, res = user_remote_proxy.userLeaveRoom(userId, roomId, UserLeaveRoomReason.USER_ACTIVE)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, '', res)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)