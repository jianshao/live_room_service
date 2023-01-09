# -*- coding:utf-8 -*-
'''
Created on 2020年11月14日

@author: zhaojiangang
'''
import fqparty
from fqparty.domain.events.events import MicRoomLoadEvent, MicRoomRemoveEvent, \
    RoomAcrossPKStartEvent, RoomAcrossPKingDataEvent, RoomPKStartEvent, \
    RoomUpdatePKRankEvent, UserOnPKLocationEvent, UserLeavePKLocationEvent, \
    RoomPKEndEvent, RoomPKExpireEvent, RoomAcrossPKEndEvent, RoomAcrossPKExpireEvent, \
    RoomPKAddCountdownEvent
from fqparty.servers.mic import MicServer
import tomato


class MicUtilsHandler(object):
    def setupEvents(self):
        fqparty.app.on(MicRoomLoadEvent, self._onRoomLoadEvent)
        fqparty.app.on(MicRoomRemoveEvent, self._onRoomRemoveEvent)

        # pk开始 送礼 都要更新跨房pk信息
        fqparty.app.on(RoomAcrossPKStartEvent, self._onRoomAcrossPKStartEvent)
        fqparty.app.on(RoomAcrossPKingDataEvent, self._onSaveAcrossPKDataEvent)
        fqparty.app.on(RoomAcrossPKEndEvent, self._onRoomAcrossPKEndEvent)
        fqparty.app.on(RoomAcrossPKExpireEvent, self._onRoomAcrossPKEndEvent)

        # pk开始 用户上下位置 送礼 都要更新团战pk信息
        fqparty.app.on(RoomPKStartEvent, self._onRoomPKStartEvent)
        fqparty.app.on(RoomPKEndEvent, self._onRoomPKEndEvent)
        fqparty.app.on(RoomPKExpireEvent, self._onRoomPKEndEvent)
        fqparty.app.on(UserOnPKLocationEvent, self._onSaveTeamPKLocationEvent)
        fqparty.app.on(UserLeavePKLocationEvent, self._onSaveTeamPKLocationEvent)
        fqparty.app.on(RoomPKAddCountdownEvent, self._onSaveTeamPKStatusEvent)
        fqparty.app.on(RoomUpdatePKRankEvent, self._onSaveTeamPKStatusEvent)

    def _onRoomLoadEvent(self, event):
        fqparty.app.utilService.clearRoomMemberHeatScore(event.activeRoom.roomId, event.activeRoom.room.guildId)
        fqparty.app.utilService.addRoomToRoomList(event.activeRoom.roomId)
        fqparty.app.utilService.addRoomToRoomTypeList(event.activeRoom.roomId, event.activeRoom.room.guildId,
                                                      event.activeRoom.room.roomType.typeId)
        MicServer.micServerActiveRoomDao.addActiveRoom(tomato.app.serverId, event.activeRoom.roomId)

    def _onRoomRemoveEvent(self, event):
        MicServer.roomMicStatusDao.removeRoomAllMicStatus(event.activeRoom.roomId)
        fqparty.app.utilService.removeRoomFromRoomList(event.activeRoom.roomId)
        fqparty.app.utilService.removeRoomFromRoomTypeList(event.activeRoom.roomId, event.activeRoom.room.guildId,
                                                           event.activeRoom.room.roomType.typeId)
        MicServer.micServerActiveRoomDao.removeActiveRoom(tomato.app.serverId, event.activeRoom.roomId)

    def _onRoomPKStartEvent(self, event):
        MicServer.roomPKLocationDao.saveRoomPKLocationMap(event.activeRoom.roomId, event.activeRoom.roomTeamPK.pkLocationMap)
        self._onSaveTeamPKStatusEvent(event)
        fqparty.app.utilService.addPKRoomList(event.activeRoom.roomId)

    def _onRoomPKEndEvent(self, event):
        # 团战pk信息存redis
        MicServer.roomTeamPKStatusDao.removeRoomTeamPKStatus(event.activeRoom.roomId)
        MicServer.roomPKLocationDao.removeRoomAllPKLocation(event.activeRoom.roomId)
        fqparty.app.utilService.removePKRoomList(event.activeRoom.roomId)
 
    def _onRoomAcrossPKStartEvent(self, event):
        fqparty.app.utilService.clearAcrossPKFinish(event.activeRoom.roomId)
        self._onSaveAcrossPKDataEvent(event)
        fqparty.app.utilService.addPKRoomList(event.activeRoom.roomId)

    def _onRoomAcrossPKEndEvent(self, event):
        fqparty.app.utilService.setAcrossPKFinish(event.activeRoom.roomId)
        MicServer.roomAcrossPKStatusDao.removeRoomAcrossPKStatus(event.activeRoom.roomId)
        fqparty.app.utilService.removePKRoomList(event.activeRoom.roomId)

    def _onSaveAcrossPKDataEvent(self, event):
        # 跨房pk信息存redis
        MicServer.roomAcrossPKStatusDao.saveRoomAcrossPKStatus(event.activeRoom.roomId, event.activeRoom.acrossRoomPK.status)

    def _onSaveTeamPKLocationEvent(self, event):
        # 团战pk位置信息存redis
        MicServer.roomPKLocationDao.saveRoomPKLocation(event.activeRoom.roomId, event.pkLocation)

    def _onSaveTeamPKStatusEvent(self, event):
        # 团战pk信息存redis
        MicServer.roomTeamPKStatusDao.saveRoomTeamPKStatus(event.activeRoom.roomId, event.activeRoom.roomTeamPK.status)


