# -*- coding:utf-8 -*-
'''
Created on 2020年11月6日

@author: zhaojiangang
'''


class UtilService(object):
    def getRoomMicCharms(self, roomId):
        raise NotImplementedError

    def setRoomMicCharm(self, roomId, micId, count):
        raise NotImplementedError

    def isKickoutUser(self, roomId, userId):
        raise NotImplementedError

    def isDisabledMsgUser(self, roomId, userId):
        raise NotImplementedError

    def getRoomLockPassword(self, roomId):
        raise NotImplementedError

    def getUserIdByToken(self, token):
        raise NotImplementedError

    def getTokenByUserId(self, userId):
        raise NotImplementedError

    def getRoomHeatScore(self, roomId):
        raise NotImplementedError

    def incrRoomChatHeatScore(self, roomId, value, isGuild):
        raise NotImplementedError

    def incrRoomMemberHeatScore(self, roomId, value, isGuild):
        raise NotImplementedError

    def addRoomToRoomList(self, roomId):
        raise NotImplementedError

    def addRoomToRoomTypeList(self, roomId, isGuild, roomType):
        raise NotImplementedError

    def removeRoomFromRoomList(self, roomId):
        raise NotImplementedError

    def removeRoomFromRoomTypeList(self, roomId, isGuild, roomType):
        raise NotImplementedError

    def addRoomUser(self, roomId, userId, userName):
        raise NotImplementedError

    def removeRoomUser(self, roomId, userId):
        raise NotImplementedError

    def getCreateAcrossPKs(self):
        raise NotImplementedError

    def setCreateAcrossPK(self, roomId, data):
        raise NotImplementedError

    def getCreateAcrossPK(self, roomId):
        raise NotImplementedError

    def delCreateAcrossPK(self, roomId):
        raise NotImplementedError

    def getAllSponsoredAcrossPK(self, roomId):
        raise NotImplementedError

    def setSponsoredAcrossPK(self, sponsoredRoomId, sponsoreRoomId, data):
        raise NotImplementedError

    def getSponsoredAcrossPK(self, sponsoredRoomId, sponsoreRoomId):
        raise NotImplementedError

    def clearExpireAcrossPK(self, roomId, pkRoomId):
        raise NotImplementedError

    def clearAcrossPKFinish(self, roomId):
        raise NotImplementedError

    def setAcrossPKFinish(self, roomId):
        raise NotImplementedError

    def getAcrossPKFinish(self, roomId):
        raise NotImplementedError

    def addPKRoomList(self, roomId):
        raise NotImplementedError

    def removePKRoomList(self, roomId):
        raise NotImplementedError

    def getUserPromoteTip(self, userId, roomId):
        """
        1V1渠道推广,进厅提示消息
        """
        raise NotImplementedError

    def addMicUser(self, roomId, micId, userId):
        raise NotImplementedError

    def removeMicUser(self, roomId, userId):
        raise NotImplementedError

    def removeAllMicUser(self, roomId):
        raise NotImplementedError
