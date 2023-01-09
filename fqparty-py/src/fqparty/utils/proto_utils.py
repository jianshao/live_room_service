# -*- coding:utf-8 -*-
'''
Created on 2020年11月14日

@author: zhaojiangang
'''
import time
from datetime import datetime
from fqparty.domain.models.room import PKTeam
from fqparty.domain.room.room import RoomMicInfo, RoomTeamPKInfo, RoomAcrossPKInfo
from fqparty.const import MicIds
from tomato.config import configure


def buildImageUrl(url):
    if (url
        and not url.startswith('http://')
        and not url.startswith('https://')):
        prefix = configure.loadJson('server.fqparty.global', {}).get('imagePrefix')
        if prefix:
            if url.startswith('/'):
                if prefix.endswith('/'):
                    return prefix[0:len(prefix) - 1] + url
            else:
                if not prefix.endswith('/'):
                    return prefix + '/' + url
            return prefix + url
    return url


def translateAttireType(attrId, attrPid):
    if attrPid == 48 or attrPid == 102:
        # 气泡/爵位气泡
        return 'bubble'
    elif attrPid == 1:
        # 头像框
        return 'avatar'
    elif attrPid == 101:
        # 麦位光圈
        return 'voiceprint'
    elif attrPid == 103:
        # 座驾
        return 'mount'
    return ''

def encodeUserWoreAttire(userWoreAttire):
    return {
        'attrId':userWoreAttire.attrId,
        'attrPid':userWoreAttire.attrPid,
        'image':buildImageUrl(userWoreAttire.imageAndroid),
        'imageIos':buildImageUrl(userWoreAttire.imageIos),
        'svga':buildImageUrl(userWoreAttire.svga),
        'color':userWoreAttire.color,
        'type': translateAttireType(userWoreAttire.attrId, userWoreAttire.attrPid),
        'multiple':float(userWoreAttire.multiple) if userWoreAttire.multiple else 0
    }

def encodeUser(user):
    return {
        'userId':user.userId,
        'name':user.nickname,
        'userName':user.userName,
        'sex':user.sex,
        'userLevel':user.userLevel,
        'headImageUrl':buildImageUrl(user.avatar),
        'isVip':user.isVip,
        'prettyId':user.prettyId,
        'prettyAvatar':buildImageUrl(user.prettyAvatar),
        'prettyAvatarSvga':buildImageUrl(user.prettyAvatarSvga),
        'attires':[attire.attrId for attire in user.attires],
        'bubble':user.bubbleAndroid,
        'bubbleIos':user.bubbleIos,
        'userAttires':[
            encodeUserWoreAttire(wa) for wa in user.woreAttires
        ],
        'dukeId':user.dukeId,
        'isNewUser': user.isNewUser,
        'guildInfo': user.guildInfo,
    }

def encodeRoomMicInfo(roomMicInfo):
    assert isinstance(roomMicInfo, RoomMicInfo)
    return {
        'micId': roomMicInfo.status.micId,
        'isLocked': roomMicInfo.status.locked,
        'isDisabled': roomMicInfo.status.disabled,
        'inviteUserId': roomMicInfo.status.inviteUserId,
        'inviteRoomId': roomMicInfo.status.inviteRoomId,
        'xinDongZhi': roomMicInfo.heartValue,
        'countdownTime': datetime.fromtimestamp(roomMicInfo.status.countdownTime).strftime('%Y-%m-%dT%H:%M:%S.0+08:00') if roomMicInfo.status.countdownTime != 0 else '',
        'countdownDuration': roomMicInfo.status.countdownDuration,
        'user': encodeUser(roomMicInfo.user) if roomMicInfo.user else None,
        'emoticonAnimationUrl': ''
    }

def encodeRoomData(activeRoom, roomStatus, roomPKMode):
    roomDesc, roomWelcomes = activeRoom.room.roomDesc, activeRoom.room.roomWelcomes

    # # 不是工会房，房间公告和房间欢迎语为空
    # if not activeRoom.room.guildId:
    #     roomDesc, roomWelcomes = '', ''

    return {
        'id':activeRoom.room.roomId,
        'prettyId':activeRoom.room.prettyRoomId,
        'ownerUserId':activeRoom.room.ownerUserId,
        'roomName':activeRoom.room.roomName,
        'roomDesc':roomDesc,
        'roomImage':buildImageUrl(activeRoom.room.backgroundImage),
        'roomWelcomes':roomWelcomes,
        'roomType':activeRoom.room.roomType.typeId,
        'roomMode':activeRoom.room.roomMode,
        'roomLock':True if activeRoom.room.roomLock else False,
        'roomDisableMsg':roomStatus.disabledMsg,
        'roomPassWord':activeRoom.room.password,
        'modeName':activeRoom.room.roomType.modeName,
        'isWheat':activeRoom.room.isWheat,
        'ModeId':activeRoom.room.roomType.typeId,
        'ModePid':activeRoom.room.roomType.parentId,
        'guildId':activeRoom.room.guildId,
        'roomPKMode': roomPKMode,
        'platformNotice': activeRoom.platformNotice,
        'MusicId':0,
        'MusicPlayerId':'',
        'MusicVolume':0,
        'MusicStatus':0,
    }

def encodeRoomPkUser(pkuser, value):
    return {
        'userId': pkuser.userId,
        'name': pkuser.nickname,
        'avater': pkuser.avatar,
        'value': value,
    }

def encodePkLocation(pkLocation):
    return {
        'location': pkLocation.location,
        'micId': pkLocation.micId,
        'isLocked': True if pkLocation.locked else False,
        'isDisabled': True if pkLocation.disabled else False,
        'duration': max(0, pkLocation.countdownTime + pkLocation.countdownDuration - int(time.time()))
    }

def encodeRoomAcrossPKData(roomAcrossPKInfo):
    assert isinstance(roomAcrossPKInfo, RoomAcrossPKInfo)
    team = roomAcrossPKInfo.getTeam()
    # charmUser = acrossRoomPK.getFirstCharmUser(team)
    # mvpUser = acrossRoomPK.getMVPUser(team)
    return {
        'team': team,  # 本房间是红队还是蓝队
        'punishment':roomAcrossPKInfo.punishment,
        # 'charmUser':encodeRoomPkUser(charmUser, charmUser.totalPkValue) if charmUser else None,
        # 'mvpUser':encodeRoomPkUser(mvpUser, mvpUser.totalContributeValue) if mvpUser else None,
        'startTime':roomAcrossPKInfo.startTime,
        'countdown':roomAcrossPKInfo.countdown,
        'duration': roomAcrossPKInfo.startTime + roomAcrossPKInfo.countdown - int(time.time()),
        'redData': {
            'roomName': roomAcrossPKInfo.acrossPK.roomName,
            'name': roomAcrossPKInfo.acrossPK.userName,
            'avater': buildImageUrl(roomAcrossPKInfo.acrossPK.userAvater),
            'pkValue': roomAcrossPKInfo.getTotalPKValue(PKTeam.RED_TEAM),
            'charmList': [encodeRoomPkUser(pkuser, pkuser.totalPkValue) for pkuser in roomAcrossPKInfo.getCharmUsers(PKTeam.RED_TEAM)],
            'contributionList': [encodeRoomPkUser(pkuser, pkuser.totalContributeValue) for pkuser in roomAcrossPKInfo.getMVPUsers(PKTeam.RED_TEAM)],
        },
        'blueData': {
            'name': roomAcrossPKInfo.status.pkUserName,
            'roomName': roomAcrossPKInfo.status.pkRoomName,
            'avater': buildImageUrl(roomAcrossPKInfo.status.pkUserAvater),
            'pkValue': roomAcrossPKInfo.getTotalPKValue(PKTeam.BLUE_TEAM),
            "charmList": [encodeRoomPkUser(pkuser, pkuser.totalPkValue) for pkuser in roomAcrossPKInfo.getCharmUsers(PKTeam.BLUE_TEAM)],
            'contributionList': [encodeRoomPkUser(pkuser, pkuser.totalContributeValue) for pkuser in roomAcrossPKInfo.getMVPUsers(PKTeam.BLUE_TEAM)]
        },
    }

def encodeRoomPKData(roomTeamPKInfo):
    assert isinstance(roomTeamPKInfo, RoomTeamPKInfo)

    charmUser = roomTeamPKInfo.getFirstCharmUser()
    mvpUser = roomTeamPKInfo.getMVPUser()
    return {
        'hostInfo': encodePkLocation(roomTeamPKInfo.getPKLocation(MicIds.pkHost)),
        'redList':[encodePkLocation(roomTeamPKInfo.getPKLocation(location)) for location in MicIds.pkRedIDs],
        'blueList':[encodePkLocation(roomTeamPKInfo.getPKLocation(location)) for location in MicIds.pkBlueIDs],
        'redTotalPKValue':sum(roomTeamPKInfo.status.redPKMap.values()),
        'blueTotalPKValue':sum(roomTeamPKInfo.status.bluePKMap.values()),
        'punishment':roomTeamPKInfo.status.punishment,
        'charmUser':encodeRoomPkUser(charmUser, charmUser.totalPkValue) if charmUser else None,
        'mvpUser':encodeRoomPkUser(mvpUser, mvpUser.totalContributeValue) if mvpUser else None,
        'startTime':roomTeamPKInfo.status.startTime,
        'countdown':roomTeamPKInfo.status.countdown,
        'duration': roomTeamPKInfo.status.startTime+roomTeamPKInfo.status.countdown-int(time.time()),
        'pkLocationCharmList': encodePKLocationCharmList(roomTeamPKInfo),
    }

def encodePKLocationCharmList(roomTeamPKInfo):
    pkLocationCharmList = []
    if roomTeamPKInfo:
        for location, pkLocation in roomTeamPKInfo.pkLocationMap.iteritems():
            item = {
                'location': location,
                'pkValue': 0
            }
            if pkLocation.userId:
                item['pkValue'] = roomTeamPKInfo.getPKValue(pkLocation.userId)
            pkLocationCharmList.append(item)
    return pkLocationCharmList

def buildRoomHeatValue(value):
    value = max(0, value)
    value = int(value)
    if value >= 10000:
        unitsScore = value / float(10000)
        if unitsScore == int(unitsScore):
            return '%dw' % int(unitsScore)
        else:
            return '%sw' % (str(unitsScore).split('.')[0] + '.' + str(unitsScore).split('.')[1][:1])
    return '%s' % (value)

def encodeRoomUserInfoOld(activeRoom, roomUserInfo, isAttention=False):
    return {
        'roomId':activeRoom.roomId,
        'isAttention':isAttention,
        'micId':roomUserInfo.micUserStatus.micId if roomUserInfo.micUserStatus else 0,
        'isDisableMsg':roomUserInfo.roomUserStatus.disabledMsg and roomUserInfo.user.dukeId < 5,
        'isDisableMicro':roomUserInfo.roomMicStatus.disabled if roomUserInfo.roomMicStatus else False,
        'isInTheRoom':True,
        'userIdentity':activeRoom.getUserIdentity(roomUserInfo.user.userId),
        'user':encodeUser(roomUserInfo.user),
        'clientInfo':roomUserInfo.sessionInfo.get('clientInfo', {}),
    }

def encodeRoomUserInfo(activeRoom, roomUserInfo):
    return {
        "micId": roomUserInfo.roomMicStatus.micId if roomUserInfo.roomMicStatus else 0,
        "userIdentity": activeRoom.getUserIdentity(roomUserInfo.user.userId),
        "userId": roomUserInfo.user.userId,
        "name": roomUserInfo.user.nickname,
        "sex": roomUserInfo.user.sex,
        "userLevel": roomUserInfo.user.userLevel,
        "headImageUrl": buildImageUrl(roomUserInfo.user.avatar),
        "isVip": roomUserInfo.user.isVip,
        "prettyId": roomUserInfo.user.prettyId,
        "dukeId": roomUserInfo.user.dukeId,
        "clientInfo": roomUserInfo.sessionInfo.get('clientInfo', {}),
    }

def getAudioValue():
    """
    获取音频配置 1：声网, 2： 即构
    """
    return configure.loadJson('server.fqparty.global', {}).get('audio', 1)
