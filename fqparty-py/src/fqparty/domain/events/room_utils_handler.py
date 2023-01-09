# -*- coding:utf-8 -*-
'''
Created on 2020年11月14日

@author: zhaojiangang
'''
import fqparty
from fqparty.proxy.room import room_remote_proxy
from fqparty.domain.events.events import UserEnterRoomEvent, UserLeaveRoomEvent, \
    PushRoomMsgEvent, SendTextMsgToRoomEvent, SendEmoticonEvent
from fqparty.utils import proto_utils
from fqparty.const import UserLeaveRoomReason
import tomato
from tomato.config import configure
from tomato.utils import strutil


class RoomUtilsHandler(object):
    def setupEvents(self):
        fqparty.app.on(UserEnterRoomEvent, self._onUserEnterRoomEvent)
        fqparty.app.on(UserLeaveRoomEvent, self._onUserLeaveRoomEvent)
        fqparty.app.on(SendTextMsgToRoomEvent, self._onSendTextMsgToRoomEvent)
        fqparty.app.on(SendEmoticonEvent, self._onSendEmoticonEvent)

    def _onUserEnterRoomEvent(self, event):
        # 房间热度
        if event.roomUser.user.dukeId >= 5:
            heatScore = self._getMemberHeatValue()
            fqparty.app.utilService.incrRoomMemberHeatScore(event.activeRoom.roomId, heatScore, event.activeRoom.room.guildId)

        fqparty.app.utilService.addRoomUser(event.activeRoom.roomId, event.roomUser.userId, '')
    
    def _onUserLeaveRoomEvent(self, event):
        if event.reason == UserLeaveRoomReason.BAN_ROOM:
            fqparty.app.utilService.clearRoomMemberHeatScore(event.activeRoom.roomId, event.activeRoom.room.guildId)
            fqparty.app.utilService.removeRoom(event.activeRoom.roomId)
        else:
            # 房间热度
            if event.roomUser.user.dukeId >= 5:
                heatScore = -1 * self._getMemberHeatValue()
                fqparty.app.utilService.incrRoomMemberHeatScore(event.activeRoom.roomId, heatScore, event.activeRoom.room.guildId)
                self._updateRoomHeatValue(event.activeRoom)

            fqparty.app.utilService.removeRoomUser(event.activeRoom.roomId, event.roomUser.userId)

    def _onSendEmoticonEvent(self, event):
        # 一分钟的聊天大于3条不计热度值
        if event.roomUser.chatInfo.chatCount > 3:
            return

        heatScore = self._getChatHeatValue()
        fqparty.app.utilService.incrRoomChatHeatScore(event.activeRoom.roomId, heatScore, event.activeRoom.room.guildId)
        self._updateRoomHeatValue(event.activeRoom)

    def _onSendTextMsgToRoomEvent(self, event):
        # 一分钟的聊天大于3条不计热度值
        if event.roomUser.chatInfo.chatCount > 3:
            return

        heatScore = self._getChatHeatValue()
        fqparty.app.utilService.incrRoomChatHeatScore(event.activeRoom.roomId, heatScore, event.activeRoom.room.guildId)
        self._updateRoomHeatValue(event.activeRoom)

    def _getMemberHeatValue(self):
        heatVules = configure.loadJson('server.fqparty.global', {}).get('heatVules', {})
        return heatVules.get('member', 0)

    def _getChatHeatValue(self):
        heatVules = configure.loadJson('server.fqparty.global', {}).get('heatVules', {})
        return heatVules.get('chat', 0)

    def _updateRoomHeatValue(self, activeRoom):
        heatValue = fqparty.app.utilService.getRoomHeatScore(activeRoom.roomId)
        msg = {
            'msgId': 2031,
            'VisitorNum': proto_utils.buildRoomHeatValue(heatValue)
        }

        msg = strutil.jsonDumps(msg)
        fqparty.app.fire(PushRoomMsgEvent(activeRoom, msg, False))

        room_remote_proxy.pushPhpMsgToAllRoomServer(activeRoom.roomId, msg, [tomato.app.serverId])


