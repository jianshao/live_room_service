# -*- coding:utf-8 -*-
'''
Created on 2020年10月22日

@author: zhaojiangang
'''

import time

import fqparty
from fqparty.domain.events.events import RoomAcrossPKStartEvent, \
    RoomAcrossPKEndEvent, RoomAcrossPKingDataEvent
from fqparty.domain.models.room import PKTeam, PKMode
from fqparty.utils import proto_utils, time_utils
from tomato.core.timer import TTTaskletTimer
from tomato.utils import ttlog, strutil, timeutil


class AcrossPK(object):
    '''创建或发起一个pk'''
    def __init__(self, createRoomId=0, createPrettyRoomId=0, pkRoomId=0, punishment='', createTime=0, countdown=0, roomName='', userName='', userAvater=''):
        # 发起pk房间id
        self.createRoomId = createRoomId
        # 发起pk房间靓号id
        self.createPrettyRoomId = createPrettyRoomId
        # 被pk
        self.pkRoomId = pkRoomId
        # 发起pk的房间名称
        self.roomName = roomName
        # 发起pk的房主的信息
        self.userName = userName
        # 发起房间的房主的信息
        self.userAvater = userAvater
        # pk惩罚描述
        self.punishment = punishment
        # 创建时间
        self.createTime = createTime
        # 倒计时时间
        self.countdown = countdown

    @property
    def duration(self):
        #发起pk的倒计时
        return max(60-(int(time.time()) - self.createTime), 0)

    def fromJson(self, data):
        self.createRoomId = data['createRoomId']
        self.createPrettyRoomId = data['createPrettyRoomId']
        self.pkRoomId = data['pkRoomId']
        self.punishment = data['punishment']
        self.createTime = data['createTime']
        self.countdown = data['countdown']
        self.roomName = data['roomName']
        self.userName = data['userName']
        self.userAvater = data['userAvater']
        return self

    def toJson(self):
        return {
            "createRoomId": self.createRoomId,
            "createPrettyRoomId": self.createPrettyRoomId,
            "pkRoomId": self.pkRoomId,
            "punishment": self.punishment,
            "createTime": self.createTime,
            "countdown": self.countdown,
            "roomName": self.roomName,
            "userName": self.userName,
            "userAvater": self.userAvater,
        }

    def toViewJson(self):
        return {
            "roomId": self.createRoomId,
            "prettyRoomId": self.createPrettyRoomId,
            "punishment": self.punishment,
            "countdown": self.countdown,
            "roomName": self.roomName,
            "duration": self.duration,
            "userAvater": proto_utils.buildImageUrl(self.userAvater)
        }


class RoomAcrossPK(object):
    def __init__(self, activeRoom, status):
        # 所属房间
        self.activeRoom = activeRoom
        self.status = status

        # 贡献榜 团战期间送礼物人的统计map(roomId, (userId, 贡献值)) 红队vs蓝队
        self.contributeMap = self.status.contributeMap

        # pk值榜 收礼物人的统计map(roomId, (userId, pk值)) 红队vs蓝队
        self.pkMap = self.status.pkMap

        self.activeRoom = activeRoom
        # 是否结束
        self._isFinish = False
        # pk的timer
        self._pkTimer = None

    @property
    def pkRoomId(self):
        return self.acrossPK.pkRoomId if self.acrossPK.createRoomId == self.activeRoom.roomId else self.acrossPK.createRoomId

    @property
    def acrossPK(self):
        return self.status.acrossPK

    @property
    def startTime(self):
        return self.status.startTime

    @property
    def punishment(self):
        return self.status.acrossPK.punishment

    @property
    def countdown(self):
        return self.status.acrossPK.countdown

    @property
    def isFinish(self):
        return self._isFinish
    
    def startPKTimer(self):
        if self._pkTimer:
            self._pkTimer.cancel()
            self._pkTimer = None

        from fqparty.servers.mic import MicServer
        countdown = self.countdown + self.startTime - int(time.time())
        self._pkTimer = TTTaskletTimer.runOnce(countdown, MicServer.micRoomService.innerEndAcrossPK, self.activeRoom.roomId)
        ttlog.info('RoomAcrossPK.startPK',
                   'roomId=', self.activeRoom.roomId,
                   'countdown=', countdown,
                   'acrossPK=', self.acrossPK.toJson())

    def stopPKTimer(self):
        if self._pkTimer:
            self._pkTimer.cancel()
            self._pkTimer = None

    def startPK(self):
        self.startPKTimer()
        fqparty.app.fire(RoomAcrossPKStartEvent(self.activeRoom))

    def endPK(self):
        if self._isFinish:
            return

        if self._pkTimer:
            self._pkTimer.cancel()

        self._isFinish = True

        redPKValue = sum(self.pkMap[self.acrossPK.createRoomId].values())
        bluePKValue = sum(self.pkMap[self.acrossPK.pkRoomId].values())

        winPK, winRoomId = None, 0
        if redPKValue > bluePKValue:
            winPK = PKTeam.RED_TEAM
            winRoomId = self.acrossPK.createRoomId
        elif bluePKValue > redPKValue:
            winPK = PKTeam.BLUE_TEAM
            winRoomId = self.acrossPK.pkRoomId

        ttlog.info('RoomAcrossPK.endPK',
                   'roomId=', self.activeRoom.roomId,
                   'winPK=', winPK,
                   'redPKValue=', redPKValue,
                   'bluePKValue=', bluePKValue)

        fqparty.app.fire(RoomAcrossPKEndEvent(self.activeRoom, self, winPK, winRoomId))

        TTTaskletTimer.runOnce(0, self.recordPKData, winPK)

    def recordPKData(self, winPK):
        try:
            redPKData = self.pkMap[self.acrossPK.createRoomId]
            redContributeData = self.contributeMap[self.acrossPK.createRoomId]

            bluePKData = self.pkMap[self.acrossPK.pkRoomId]
            blueContributeData = self.contributeMap[self.acrossPK.pkRoomId]

            redPKData = strutil.jsonDumps(redPKData)
            redContributeData = strutil.jsonDumps(redContributeData)
            bluePKData = strutil.jsonDumps(bluePKData)
            blueContributeData = strutil.jsonDumps(blueContributeData)

            from fqparty.servers.mic import MicServer
            MicServer.pkDao.addPK(self.acrossPK.createRoomId, self.acrossPK.pkRoomId, PKMode.ACROSS_PK,
                                        self.startTime, int(time.time()), self.punishment, winPK, redPKData,
                                        redContributeData, bluePKData, blueContributeData)
        except:
            ttlog.warn('RoomAcrossPK.endPK addPK error',
                        'roomId=', self.activeRoom.roomId,
                        'redRoomId=', self.acrossPK.createRoomId,
                        'blueRoomId=', self.acrossPK.pkRoomId,
                        'createTime=', self.startTime,
                        'punishment=', self.punishment,
                        'pkMap=', self.pkMap,
                        'contributeMap=', self.contributeMap.keys())

    def updatePKRoomData(self, pkDataMap, contributeDataMap):
        '''同步pk房间的数据'''
        for userId, pkValue in pkDataMap.iteritems():
            self.pkMap[self.pkRoomId][userId] = pkValue

        for userId, contributeValue in contributeDataMap.iteritems():
            self.contributeMap[self.pkRoomId][userId] = contributeValue

        ttlog.debug('RoomAcrossPK.updatePKRoomData',
                    'roomId=', self.activeRoom.roomId,
                    'pkMap=', self.pkMap,
                    'contributeMap=', self.contributeMap)

        fqparty.app.fire(RoomAcrossPKingDataEvent(self.activeRoom, None))

    def sendGift(self, dmsg):
        # 只处理本房间的 本房间结束和pk房间结束 都不加数据
        if dmsg['roomId'] != self.activeRoom.roomId \
                or self._isFinish \
                or fqparty.app.utilService.getAcrossPKFinish(self.pkRoomId):
            return

        if not self.isActivityExpire() and dmsg.get('fromBag'):
            # 活动期间从背包送礼的不计pk值
            ttlog.info('RoomAcrossPK.sendGift',
                       'roomId=', self.activeRoom.roomId,
                       'fromBag=', dmsg['fromBag'])
            return

        sendUserId = str(dmsg['GiftGiver']['UserId'])
        sendUserName = dmsg['GiftGiver']['Name']
        sendUserAvatar = dmsg['GiftGiver']['HeadImageUrl']

        totalPrice = int(dmsg['Count'] * dmsg['GiftData']['Price'])
        totalCharm = int(dmsg['Count'] * dmsg['GiftData'].get('Charm', 0))

        if totalPrice == 0:
            # 没有价值的礼物不需要处理
            ttlog.info('RoomAcrossPK.sendGift',
                       'roomId=', self.activeRoom.roomId,
                       'giftName=', dmsg['GiftData']['Name'])
            return

        for receiveData in dmsg.get('GiveGiftDatas', []):
            receiveId = str(receiveData['userId'])
            mic = self.activeRoom.findMic(receiveData['micId'])
            if not mic or not mic.status.userId:
                ttlog.warn("sendGift wain sendUserId = ", sendUserId,
                           'roomId=', self.activeRoom.roomId,
                           "receiveId=", receiveId,
                           "micId=", receiveData['micId'])
                continue

            # 送礼人累加贡献值
            contributeMap = self.contributeMap[self.activeRoom.roomId]
            if sendUserId not in contributeMap:
                contributeMap[sendUserId] = totalPrice
            else:
                contributeMap[sendUserId] += totalPrice

            # 收礼人累加PK值
            pkMap = self.pkMap[self.activeRoom.roomId]
            if receiveId not in pkMap:
                pkMap[receiveId] = totalCharm
            else:
                pkMap[receiveId] += totalCharm

            ttlog.info('RoomAcrossPK.sendGift',
                       'roomId=', self.activeRoom.roomId,
                       'pkRoomId=', self.pkRoomId,
                       'sendUserId=', sendUserId,
                       'receiveUserId', receiveId,
                       'giftId=', dmsg['GiftId'],
                       'count=', dmsg['Count'],
                       'totalPrice=', totalPrice,
                       'pkMap=', self.pkMap[self.activeRoom.roomId],
                       'contributeMap=', self.contributeMap[self.activeRoom.roomId])

        fqparty.app.fire(RoomAcrossPKingDataEvent(self.activeRoom, None))

        # 同步pk房间信息
        from fqparty.servers.mic import MicServer
        activeRoom = MicServer.activeRoomManager.findActiveRoom(self.pkRoomId)
        pkDataMap = self.pkMap[self.activeRoom.roomId]
        contributeDataMap = self.contributeMap[self.activeRoom.roomId]
        if activeRoom:
            activeRoom.updatePKRoomData(pkDataMap, contributeDataMap)
        else:
            from fqparty.proxy.mic import mic_remote_proxy
            mic_remote_proxy.updatePKRoomData(self.pkRoomId, pkDataMap, contributeDataMap)

    def isActivityExpire(self):
        # 是否活动期
        startTime = fqparty.app.utilService.getAcrossPKActivity('start_time')
        stopTime = fqparty.app.utilService.getAcrossPKActivity('stop_time')
        if not startTime or not stopTime:
            return True

        startTime = time_utils.getTimeStampFromStr(startTime)
        stopTime = time_utils.getTimeStampFromStr(stopTime)
        timestamp = time_utils.getCurrentTimestamp()
        if timestamp < startTime or timestamp > stopTime:
            return True

        # 没过期 判断时间段
        periodTime = fqparty.app.utilService.getAcrossPKActivity('period_time')
        if periodTime:
            periodTime = strutil.jsonLoads(periodTime)
            currentStr = time_utils.formatTimeDay()

            startTimePoint = time_utils.getTimeStampFromStr(currentStr + ' ' + periodTime[0])
            stopTimePoint = time_utils.getTimeStampFromStr(currentStr + ' ' + periodTime[1])

            if timestamp < startTimePoint or timestamp > stopTimePoint:
                return True

        return False


class RoomAcrossPKStatus(object):
    def __init__(self, acrossPK=None, startTime=0):
        # 创建的pk
        self.acrossPK = acrossPK
        # 被pk的房间信息
        self.pkRoomName = ''
        self.pkUserName = ''
        self.pkUserAvater = ''
        # 开始时间
        self.startTime = startTime

        # 贡献榜 团战期间送礼物人的统计map(roomId, (userId, 贡献值)) 红队vs蓝队
        self.contributeMap = {}
        if self.acrossPK:
            self.contributeMap[self.acrossPK.createRoomId] = {}
            self.contributeMap[self.acrossPK.pkRoomId] = {}

        # pk值榜 收礼物人的统计map(roomId, (userId, pk值)) 红队vs蓝队
        self.pkMap = {}
        if self.acrossPK:
            self.pkMap[self.acrossPK.createRoomId] = {}
            self.pkMap[self.acrossPK.pkRoomId] = {}

    def isExpire(self):
        # 判断pk是否过期
        currentTime = timeutil.currentTimestamp()
        return currentTime >= self.startTime + self.acrossPK.countdown

    def toDict(self):
        return {
            'acrossPK': self.acrossPK.toJson(),
            'pkRoomName': self.pkRoomName,
            'pkUserName': self.pkUserName,
            'pkUserAvater': self.pkUserAvater,
            'startTime': self.startTime,
            'contributeMap': self.contributeMap,
            'pkMap': self.pkMap,
        }

    def fromDict(self, d):
        contributeMap = {}
        for roomId, map in d['contributeMap'].iteritems():
            contributeMap[int(roomId)] = map

        pkMap = {}
        for roomId, map in d['pkMap'].iteritems():
            pkMap[int(roomId)] = map

        self.acrossPK = AcrossPK().fromJson(d['acrossPK'])
        self.pkRoomName = d['pkRoomName']
        self.pkUserName = d['pkUserName']
        self.pkUserAvater = d['pkUserAvater']
        self.startTime = d['startTime']
        self.contributeMap = contributeMap
        self.pkMap = pkMap
        return self


class RoomAcrossPKStatusDao(object):
    def loadRoomAcrossPKStatus(self, roomId):
        '''
        加载跨房pk
        @return: RoomAcrossPKStatus or None
        '''
        raise NotImplementedError

    def saveRoomAcrossPKStatus(self, roomId, roomAcrossPKStatus):
        '''
        保存跨房pk
        '''
        raise NotImplementedError

    def removeRoomAcrossPKStatus(self, roomId):
        '''
        删除跨房pk
        '''
        raise NotImplementedError




