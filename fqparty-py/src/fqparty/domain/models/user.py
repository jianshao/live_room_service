# -*- coding:utf-8 -*-
'''
Created on 2020年10月28日

@author: zhaojiangang
'''

from fqparty.utils import time_utils


class UserAttire(object):
    def __init__(self, attrId=None, isWore=False):
        self.attrId = attrId
        self.isWore = isWore


class UserWoreAttire(object):
    def __init__(self):
        self.attrId = None
        self.kindId = None
        self.attrPid = None
        self.attrType = None
        self.imageIos = None
        self.imageAndroid = None
        self.svga = None
        self.color = ''
        self.multiple = ''
    
    def toDict(self):
        return {
            'attrId':self.attrId,
            'kindId': self.kindId,
            'attrPid':self.attrPid,
            'attrType':self.attrType,
            'imageIos':self.imageIos,
            'imageAndroid':self.imageAndroid,
            'svga':self.svga,
            'color':self.color,
            'multiple':self.multiple,
        }
    
    def fromDict(self, d):
        self.attrId = d['attrId']
        self.kindId = d['kindId']
        self.attrPid = d['attrPid']
        self.attrType = d['attrType']
        self.imageIos = d['imageIos']
        self.imageAndroid = d['imageAndroid']
        self.svga = d['svga']
        self.color = d['color']
        self.multiple = d['multiple']
        return self


class User(object):
    def __init__(self, userId=0):
        self.userId = userId
        self.userName = ''
        self.password = ''
        self.nickname = ''
        self.sex = 0
        self.isVip = 0
        self.role = 0
        self.userLevel = 0
        self.avatar = ''
        self.prettyId = 0
        self.prettyAvatar = ''
        self.prettyAvatarSvga = ''
        self.bubbleIos = ''
        self.bubbleAndroid = ''
        self.attires = []
        self.woreAttires = []
        self.dukeId = 0
        self.attestation = 0  # 0 未提交 1认证 2未通过 3审核中
        self.registerTime = 0  # 注册时间
        self.guildInfo = {}  # 公会信息

    @property
    def isNewUser(self):
        return time_utils.getCurrentTimestamp() - self.registerTime < 86400 * 2

    def toDict(self):
        return {
            'userId':self.userId,
            'userName':self.userName,
            'password':self.password,
            'nickname':self.nickname,
            'sex':self.sex,
            'isVip':self.isVip,
            'role':self.role,
            'userLevel':self.userLevel,
            'avatar':self.avatar,
            'prettyId':self.prettyId,
            'prettyAvatar':self.prettyAvatar,
            'prettyAvatarSvga':self.prettyAvatarSvga,
            'attires':[{'attrId':ua.attrId, 'isWare':ua.isWore} for ua in self.attires],
            'bubbleIos':self.bubbleIos,
            'bubbleAndroid':self.bubbleAndroid,
            'woreAttires':[wa.toDict() for wa in self.woreAttires],
            'dukeId':self.dukeId,
            'attestation': self.attestation,
            'registerTime': self.registerTime,
            'guildInfo': self.guildInfo,
        }
        
    def fromDict(self, d):
        self.userId = d['userId']
        self.userName = d['userName']
        self.password = d['password']
        self.nickname = d['nickname']
        self.sex = d['sex']
        self.isVip = d['isVip']
        self.role = d['role']
        self.userLevel = d['userLevel']
        self.avatar = d['avatar']
        self.prettyId = d['prettyId']
        self.prettyAvatar = d['prettyAvatar']
        self.prettyAvatarSvga = d['prettyAvatarSvga']
        self.attires = [UserAttire(ua.get('attrId'), ua.get('isWore')) for ua in d['attires']]
        self.bubbleIos = d['bubbleIos']
        self.bubbleAndroid = d['bubbleAndroid']
        self.woreAttires = [UserWoreAttire().fromDict(wad) for wad in d['woreAttires']]
        self.dukeId = d['dukeId']
        self.attestation = d.get('attestation', 0)
        self.registerTime = d.get('registerTime', 0)
        self.guildInfo = d.get('guildInfo', {})
        return self


class UserAttireDao(object):
    def loadUserAttires(self, userId):
        '''
        加载用户所有装扮
        @return: list<UserAttire>
        '''
        raise NotImplementedError


class UserDao(object):
    def loadUser(self, userId):
        '''
        加载用户数据
        @return: User/None
        '''
        raise NotImplementedError


class UserFrontDao(object):
    def getFrontendId(self, userId):
        '''
        获取用户长连接的serverId
        '''
        raise NotImplementedError

    def setFrontendId(self, userId, frontendId):
        '''
        设置用户长连接serverId
        '''
        raise NotImplementedError
    
    def removeFrontendId(self, userId):
        '''
        删除用户长连接serverId
        '''
        raise NotImplementedError


class UserCacheDao(object):
    def saveUser(self, user):
        '''
        保存用户信息到缓存
        '''
        raise NotImplementedError
    
    def loadUser(self, userId):
        '''
        从缓存加载用户信息
        '''
        raise NotImplementedError


class SessionInfoDao(object):
    def loadSessionInfo(self, userId):
        '''
        加载用户的sessionInfo
        '''
        raise NotImplementedError
    
    def saveSessionInfo(self, userId, sessionInfo):
        '''
        保存用户的sessionInfo
        '''
        raise NotImplementedError

