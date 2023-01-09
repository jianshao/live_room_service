# -*- coding:utf-8 -*-
'''
Created on 2021年1月29日

@author: zhaojiangang
'''
import fqparty
from fqparty.domain.events.events import UserHeartbeatEvent, UserLeaveRoomEvent
from fqparty.utils import phpapi, time_utils


class RoomOnlineHandler(object):
    def __init__(self):
        self._setupEvents()

    def _setupEvents(self):
        fqparty.app.on(UserHeartbeatEvent, self._onUserHeartbeatEvent)
        fqparty.app.on(UserLeaveRoomEvent, self._onUserLeaveRoomEvent)

    def _onUserLeaveRoomEvent(self, event):
        try:
            duration = time_utils.getCurrentTimestamp() - event.roomUser.lastHeartbeatTime
            phpapi.notifyRoomOnline(event.roomUser.userId, event.roomUser.roomId, max(0, duration))
        except:
            pass

    def _onUserHeartbeatEvent(self, event):
        try:
            phpapi.notifyRoomOnline(event.roomUser.userId, event.roomUser.roomId, max(0, event.duration))
        except:
            pass


