# -*- coding:utf-8 -*-
'''
Created on 2020年10月22日

@author: zhaojiangang
'''

import time

import fqparty
from fqparty.const import MicIds
from fqparty.domain.models.room import PKTeam, PKMode
from fqparty.domain.events.events import RoomPKStartEvent, RoomPKEndEvent, RoomPKAddCountdownEvent, RoomUpdatePKRankEvent
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog, strutil, timeutil


class RoomTeamPK(object):
    def __init__(self, activeRoom, status):
        self.activeRoom = activeRoom
        self.status = status

        # pk坑位列表map<micId, RoomMic>
        self.pkLocationList = self.loadPKLocationList()
        self.pkLocationMap = {pkLocation.location: pkLocation for pkLocation in self.pkLocationList}

        # 是否结束
        self._isFinish = False
        # pk的timer
        self._pkTimer = None

    @property
    def isFinish(self):
        return self._isFinish
    
    def loadPKLocationList(self):
        pkLocationList, _isSave = [], False
        from fqparty.servers.mic import MicServer
        pkLocationMap = MicServer.roomPKLocationDao.loadRoomPKLocationMap(self.activeRoom.roomId, MicIds.pkIDs)
        # 目前是9麦，可以根据房间类型进行处理
        for locationId in MicIds.pkIDs:
            pkLocation = pkLocationMap.get(locationId)
            if not pkLocation:
                pkLocation = RoomPKLocation(locationId)

            pkLocationList.append(pkLocation)

        return pkLocationList

    # 是否加入过该队 location可以知道在那个队 如果在红/蓝队中获得了pk值才算加入过 如果上的位置是红队的位置 要判断在蓝队中有没有pkvlaue
    def canJoin(self, userId, location):
        userId = str(userId)
        if location in MicIds.pkRedIDs:
            return userId not in self.status.bluePKMap.keys()
        elif location in MicIds.pkBlueIDs:
            return userId not in self.status.redPKMap.keys()
        else:
            return userId not in self.status.bluePKMap.keys() and userId not in self.status.redPKMap.keys()

    def getPKValue(self, userId):
        userId = str(userId)
        if userId in self.status.bluePKMap.keys():
            return self.status.bluePKMap[userId]
        elif userId in self.status.redPKMap.keys():
            return self.status.redPKMap[userId]
        return 0

    def getPKLocation(self, location):
        return self.pkLocationMap.get(location)

    def getPKLocationByMicId(self, micId):
        for pkLocation in self.pkLocationList:
            if pkLocation.micId == micId:
                return pkLocation
        return None
    
    def getPKLocationByUserId(self, userId):
        for pkLocation in self.pkLocationList:
            if pkLocation.userId == userId:
                return pkLocation
        return None

    def stopPKTimer(self):
        if self._pkTimer:
            self._pkTimer.cancel()

    def startPKTimer(self):
        if self._pkTimer:
            self._pkTimer.cancel()
            self._pkTimer = None

        from fqparty.servers.mic import MicServer
        countdown = self.status.countdown + self.status.startTime - int(time.time())
        self._pkTimer = TTTaskletTimer.runOnce(countdown, MicServer.micRoomService.innerEndPK, self.activeRoom.roomId)

        ttlog.info('RoomPK.startTimer',
                   'roomId=', self.activeRoom.roomId,
                   'startTime=', self.status.startTime,
                   'countdown=', self.status.countdown,
                   'countdown=', countdown)

        return countdown

    def startPK(self):
        self.startPKTimer()
        fqparty.app.fire(RoomPKStartEvent(self.activeRoom))

    def endPK(self):
        if self._isFinish:
            return

        if self._pkTimer:
            self._pkTimer.cancel()

        self._isFinish = True
        redPKValue = sum(self.status.redPKMap.values())
        bluePKValue = sum(self.status.bluePKMap.values())

        winPK = None
        if redPKValue > bluePKValue:
            winPK = PKTeam.RED_TEAM
        elif bluePKValue > redPKValue:
            winPK = PKTeam.BLUE_TEAM

        roomId = self.activeRoom.roomId
        ttlog.info('RoomPK.endPK',
                   'roomId=', roomId,
                   'winPK=', winPK,
                   'redPKValue=', redPKValue,
                   'bluePKValue=', bluePKValue,
                   'pkUsers=', [(pkLocation.location, pkLocation.userId) for pkLocation in self.pkLocationList])

        fqparty.app.fire(RoomPKEndEvent(self.activeRoom, self, winPK))

        TTTaskletTimer.runOnce(0, self.recordPKData, winPK)

    def recordPKData(self, winPK):
        try:
            endTime = int(time.time())
            if endTime - self.status.startTime < 60 and sum(self.status.redPKMap.values())+sum(self.status.bluePKMap.values()) == 0:
                # 小于1分钟 没有值的不存数据
                return

            from fqparty.servers.mic import MicServer
            redPKData = strutil.jsonDumps(self.status.redPKMap)
            redContributeData = strutil.jsonDumps(self.status.redContributeMap)
            bluePKData = strutil.jsonDumps(self.status.bluePKMap)
            blueContributeData = strutil.jsonDumps(self.status.blueContributeMap)
            MicServer.pkDao.addPK(self.activeRoom.roomId, self.activeRoom.roomId, PKMode.TEAM_PK, self.status.startTime,
                                        int(time.time()), self.status.punishment, winPK, redPKData, redContributeData,
                                        bluePKData, blueContributeData)
        except:
            ttlog.error('RoomPK.endPK addPK error',
                        'roomId=', self.activeRoom.roomId,
                        'createTime=', self.status.startTime,
                        'punishment=', self.status.punishment,
                        'winPK=', winPK,
                        'redPKData=', self.status.redPKMap,
                        'redContributeData=', self.status.redContributeMap,
                        'bluePKData=', self.status.bluePKMap,
                        'blueContributeDat=', self.status.blueContributeMap)

    def addPKCountdown(self, duration):
        if self._pkTimer:
            self._pkTimer.cancel()

        # 新的倒计时时间
        self.status.countdown += duration
        countdown = self.startPKTimer()

        ttlog.info('RoomPK.addPKCountdown',
                   'roomId=', self.activeRoom.roomId,
                   'startTime=', self.status.startTime,
                   'countdown=', self.status.countdown,
                   'duration=', duration,
                   'countdown=', countdown)

        fqparty.app.fire(RoomPKAddCountdownEvent(self.activeRoom, countdown))

    def sendGift(self, dmsg):
        # 只处理本房间的
        if dmsg['roomId'] != self.activeRoom.roomId or self._isFinish:
            return

        sendUserId = str(dmsg['GiftGiver']['UserId'])
        totalPrice = int(dmsg['Count']) * int(dmsg['GiftData']['Price'])
        totalCharm = int(dmsg['Count']) * int(dmsg['GiftData'].get('Charm', 0))

        if totalPrice == 0:
            # 没有价值的礼物不需要处理
            ttlog.info('RoomPK.sendGift',
                       'roomId=', self.activeRoom.roomId,
                       'giftName=', dmsg['GiftData']['Name'])
            return

        pkLoaction = self.getPKLocationByUserId(int(sendUserId))
        isHost = pkLoaction and pkLoaction.location == MicIds.pkHost

        for receiveData in dmsg.get('GiveGiftDatas', []):
            pkLoaction = self.getPKLocationByMicId(receiveData['micId'])
            if not pkLoaction or not pkLoaction.userId:
                ttlog.warn("sendGift wain sendUserId = ", sendUserId,
                           'roomId=', self.activeRoom.roomId,
                           "micId=", receiveData['micId'])
                continue

            receiveId = str(pkLoaction.userId)

            # 主持麦上送礼人累加贡献值
            if isHost:
                if sendUserId in self.status.hostContributeMap:
                    self.status.hostContributeMap[sendUserId] += totalPrice
                else:
                    self.status.hostContributeMap[sendUserId] = totalPrice

            if pkLoaction.location in MicIds.pkRedIDs:
                # 送礼人累加贡献值
                if sendUserId in self.status.redContributeMap:
                    self.status.redContributeMap[sendUserId] += totalPrice
                else:
                    self.status.redContributeMap[sendUserId] = totalPrice

                # 收礼人累加PK值
                if receiveId in self.status.redPKMap:
                    self.status.redPKMap[receiveId] += totalCharm
                else:
                    self.status.redPKMap[receiveId] = totalCharm
            elif pkLoaction.location in MicIds.pkBlueIDs:
                # 送礼人累加贡献值
                if sendUserId in self.status.blueContributeMap:
                    self.status.blueContributeMap[sendUserId] += totalPrice
                else:
                    self.status.blueContributeMap[sendUserId] = totalPrice

                # 收礼人累加PK值
                if receiveId in self.status.bluePKMap:
                    self.status.bluePKMap[receiveId] += totalCharm
                else:
                    self.status.bluePKMap[receiveId] = totalCharm

            ttlog.info('RoomPK.sendGift',
                       'roomId=', self.activeRoom.roomId,
                       'sendUserId=', sendUserId,
                       'receiveUserId=', receiveId,
                       'giftId=', dmsg['GiftId'],
                       'count=', dmsg['Count'],
                       'totalPrice=', totalPrice,
                       'micId=', receiveData['micId'],
                       'location_micId=', pkLoaction.micId,
                       'location=', pkLoaction.location,
                       'hostContributeMap=', self.status.hostContributeMap,
                       'redContributeMap=', self.status.redContributeMap,
                       'blueContributeMap=', self.status.blueContributeMap,
                       'redPKMap=', self.status.redPKMap,
                       'bluePKMap=', self.status.bluePKMap,
                       'pkUsers=', [(pkLocation.location, pkLocation.userId) for pkLocation in self.pkLocationList])

        fqparty.app.fire(RoomUpdatePKRankEvent(self.activeRoom))


class RoomPKLocation(object):
    def __init__(self, location=0):
        # pk的坑位
        self.location = location
        # 是否锁麦
        self.locked = False
        # 是否禁麦
        self.disabled = False
        # 开始时间
        self.countdownTime = 0
        # 倒计时时间
        self.countdownDuration = 0
        # 邀请的用户ID
        self.inviteUserId = 0
        self.inviteRoomId = 0
        # 当前房间里的真实麦位
        self.micId = 0
        # 坑位上的用户ID
        self.userId = 0

    def toDict(self):
        return {
            'location': self.location,
            'micId': self.micId,
            'locked': self.locked,
            'disabled': self.disabled,
            'countdownTime': self.countdownTime,
            'countdownDuration': self.countdownDuration,
            'inviteUserId': self.inviteUserId,
            'inviteRoomId': self.inviteRoomId,
            'userId': self.userId,
        }

    def fromDict(self, d):
        self.location = d['location']
        self.micId = d['micId']
        self.locked = d['locked']
        self.disabled = d['disabled']
        self.countdownTime = d['countdownTime']
        self.countdownDuration = d['countdownDuration']
        self.inviteUserId = d['inviteUserId']
        self.inviteRoomId = d['inviteRoomId']
        self.userId = d['userId']
        return self


class RoomPKLocationDao(object):
    def loadRoomPKLocationMap(self, roomId, locationIds, needInit=True):
        '''
        加载房间pk坑位列表
        needInit: 如果PKLocation不存在需要初始化
        @return: map<micId, RoomPKLocation>
        '''
        raise NotImplementedError

    def saveRoomPKLocationMap(self, roomId, roomPKLocationMap):
        '''
        保存房间pk坑位列表
        '''
        raise NotImplementedError

    def loadRoomPKLocation(self, roomId, locationId):
        '''
        加载房间pk坑位
        @return: map<micId, RoomPKLocation>
        '''
        raise NotImplementedError

    def saveRoomPKLocation(self, roomId, roomPKLocation):
        '''
        保存房间pk坑位
        '''
        raise NotImplementedError

    def removeRoomAllPKLocation(self, roomId):
        '''
        删除房间pk坑位列表
        '''
        raise NotImplementedError


class RoomTeamPKStatus(object):
    def __init__(self):
        # pk惩罚描述
        self.punishment = None
        # 开始时间
        self.startTime = 0
        # 总的倒计时时间
        self.countdown = 0

        # 贡献榜 团战期间送礼物人的统计map(userId, 贡献值) 红队vs蓝队
        self.hostContributeMap = {}  # 主持位上贡献
        self.redContributeMap = {}
        self.blueContributeMap = {}

        # pk值榜 收礼物人的统计map(userId, pk值) 红队vs蓝队
        self.redPKMap = {}
        self.bluePKMap = {}

    def isExpire(self):
        # 判断pk是否过期
        currentTime = timeutil.currentTimestamp()
        return currentTime >= self.startTime + self.countdown

    def toDict(self):
        return {
            'punishment': self.punishment,
            'startTime': self.startTime,
            'countdown': self.countdown,
            'redPKMap': self.redPKMap,
            'bluePKMap': self.bluePKMap,
            'hostContributeMap': self.hostContributeMap,
            'redContributeMap': self.redContributeMap,
            'blueContributeMap': self.blueContributeMap,
        }

    def fromDict(self, d):
        self.punishment = d['punishment']
        self.startTime = d['startTime']
        self.countdown = d['countdown']
        self.redPKMap = d['redPKMap']
        self.bluePKMap = d['bluePKMap']
        self.hostContributeMap = d['hostContributeMap']
        self.redContributeMap = d['redContributeMap']
        self.blueContributeMap = d['blueContributeMap']
        return self


class RoomTeamPKStatusDao(object):
    def loadRoomTeamPKStatus(self, roomId):
        '''
        加载团战pk
        @return: MicUserStatus or None
        '''
        raise NotImplementedError

    def saveRoomTeamPKStatus(self, roomId, roomTeamPK):
        '''
        保存团战pk
        '''
        raise NotImplementedError

    def removeRoomTeamPKStatus(self, roomId):
        '''
        删除团战pk
        '''
        raise NotImplementedError





