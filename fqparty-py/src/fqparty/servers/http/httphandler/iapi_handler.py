# -*- coding:utf-8 -*-
'''
Created on 2020年11月3日

@author: zhaojiangang
'''
import fqparty
from fqparty.const import HttpResponseCode, ErrorCode
from fqparty.decorator.decorator import exceptionHandlerOld
from fqparty.proxy.room import room_remote_proxy
from fqparty.proxy.user import user_remote_proxy
from fqparty.proxy.mic import mic_remote_proxy
from fqparty.utils import http_util
from fqparty.utils.http_util import HttpJsonForm
from tomato.core.exceptions import TTException
from tomato.decorator.decorator import httpJsonHandler


@httpJsonHandler(path='/iapi/disableMsg')
@exceptionHandlerOld
def disableRoomUserMsg(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        toUserId = int(form.getStringParam('toUserId'))
        isDisabled = form.getIntParam('isDisabled')
        ec, res = room_remote_proxy.disableUserMsg(roomId, toUserId, isDisabled == 1)
        if ec != 0:
            raise TTException(ec, res)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)
    
@httpJsonHandler(path='/iapi/kickout')
@exceptionHandlerOld
def kickoutUser(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        toUserId = int(form.getStringParam('toUserId'))
        ec, res = user_remote_proxy.kickoutRoomUser(toUserId, roomId)
        if ec != 0:
            raise TTException(ec, res)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/broadcast')
@exceptionHandlerOld
def broadcastMsgToRoom(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        toUserId = int(form.getStringOptionParam('toUserId', '0'))
        fromRoomId = form.getIntOptionParam('fromRoomId', 0)
        fromUserId = form.getIntOptionParam('fromUserId', 0)
        msg = form.getStringParam('msg')
        if roomId != 0:
            if toUserId <= 0:
                room_remote_proxy.pushMsgToRoom(roomId, msg)
                mic_remote_proxy.pushMsgToRoom(roomId, msg)
            else:
                room_remote_proxy.sendRoomMsgToUser(roomId, toUserId, msg)
        else:
            excludeRoomIds = [fromRoomId] if fromRoomId != 0 else []
            excludeUserIds = [fromUserId] if fromUserId != 0 else []
            room_remote_proxy.pushMsgToAllRoom(msg, excludeRoomIds, excludeUserIds)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/broadcastLed')
@exceptionHandlerOld
def broadcastLedMsgToRoom(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        fromRoomId = form.getIntOptionParam('fromRoomId', 0)
        fromUserId = form.getIntOptionParam('fromUserId', 0)
        msg = form.getStringParam('msg')
        if roomId != 0:
            room_remote_proxy.pushMsgToRoom(roomId, msg, 'led')
        else:
            excludeRoomIds = [fromRoomId] if fromRoomId != 0 else []
            excludeUserIds = [fromUserId] if fromUserId != 0 else []
            room_remote_proxy.pushMsgToAllRoom(msg, excludeRoomIds, excludeUserIds, 'led')
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/lockRoom')
@exceptionHandlerOld
def lockRoom(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        locked = form.getIntParam('lock') == 1
        room_remote_proxy.lockRoom(roomId, locked)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/updateUserInfo')
@exceptionHandlerOld
def updateUserInfo(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
        ec, res = user_remote_proxy.updateUserInfo(userId)
        if ec != 0:
            raise TTException(ec, res)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)
    
@httpJsonHandler(path='/iapi/syncRoomData')
@exceptionHandlerOld
def syncRoomData(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        dataType = form.getStringParam('type')
        ec, res = mic_remote_proxy.syncRoomData(roomId, dataType)
        if ec != 0:
            raise TTException(ec, res)

        room_remote_proxy.syncRoomData(roomId, dataType)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/syncUserData')
@exceptionHandlerOld
def syncUserData(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
        ec, res = user_remote_proxy.updateUserInfo(userId)
        if ec != 0:
            raise TTException(ec, res)
        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/checkUserLogin')
@exceptionHandlerOld
def checkUserLogin(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
        user_remote_proxy.checkUserLogin(userId, None)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/globalUserNotify')
@exceptionHandlerOld
def globalUserNotify(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
        msg = form.getStringParam('msg')

        # user_remote_proxy.globalUserNotify(userId, msg)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/lockMic')
@exceptionHandlerOld
def iapiLockMic(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
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

@httpJsonHandler(path='/iapi/banMic')
@exceptionHandlerOld
def iapiBanMic(request):
    try:
        form = HttpJsonForm(request)
        userId = form.getIntParam('userId')
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

@httpJsonHandler(path='/iapi/endAcrossPK')
@exceptionHandlerOld
def endAcrossPK(request):
    try:
        form = HttpJsonForm(request)
        createRoomId = form.getIntParam('createRoomId')
        pkRoomId = form.getIntParam('pkRoomId')
        ec, res = mic_remote_proxy.endAcrossPK(createRoomId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        ec, res = mic_remote_proxy.endAcrossPK(pkRoomId)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/startAcrossPK')
@exceptionHandlerOld
def startAcrossPK(request):
    try:
        form = HttpJsonForm(request)
        createRoomId = form.getIntParam('createRoomId')
        pkRoomId = form.getIntParam('pkRoomId')
        punishment = form.getStringParam('punishment')
        countdown = form.getIntParam('countdown')
        ec, res = mic_remote_proxy.innerStartAcrossPK(createRoomId, createRoomId, pkRoomId, punishment, countdown)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        ec, res = mic_remote_proxy.innerStartAcrossPK(pkRoomId, createRoomId, pkRoomId, punishment, countdown)
        if ec != 0:
            return http_util.makeResponseOld(ec, res, None)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

@httpJsonHandler(path='/iapi/banRoom')
@exceptionHandlerOld
def banRoom(request):
    try:
        form = HttpJsonForm(request)
        roomId = form.getIntParam('roomId')
        operator = form.getIntParam('operator')
        reasonInfo = form.getStringOptionParam('reasonInfo')
        isBan = form.getIntParam('isBan') == 1
        if not isBan:
            fqparty.app.utilService.removeBanRoom(roomId)
        else:
            ec, res = mic_remote_proxy.banRoom(roomId,  operator, reasonInfo)
            # 跨房pk中 不能封禁
            if ec == ErrorCode.ACORSS_ROOM_EXISTS:
                return http_util.makeResponseOld(ec, res, None)

            fqparty.app.utilService.addBanRoom(roomId)

        return http_util.makeResponseOld(HttpResponseCode.SUCCESS, 'ok', None)
    except ValueError:
        raise TTException(ErrorCode.BAD_PARAMS)

