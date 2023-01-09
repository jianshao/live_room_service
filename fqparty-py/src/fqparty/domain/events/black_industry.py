# coding=utf-8
import time
from tomato.utils import ttlog
from fqparty.servers.room import RoomServer
from fqparty.utils import phpapi, time_utils
import cachetools.func

FILTER_PROTECT_USER = 1
FILTER_HEICHAN_USER = 2


# 处理2中情况：
# 1.将受保护用户的信息从消息内容中过滤掉（查看用户列表）
# 2.在广播消息的接受列表中过滤掉黑产用户（公屏消息/进出房通知等）
class BlackIndustryStrategy(object):

    def __init__(self, userId, userIdList, eventType):
        # 根据eventType判断是哪种情况
        self.userId = userId
        self.userIdList = userIdList
        self.eventType = eventType
        self.isBlock, self.isSensitive = self.isBlockedUser(self.userId)

    def afterFilter(self):
        if self.eventType == FILTER_PROTECT_USER:
            # 先判断userId是不是黑产用户
            if not self.isBlock:
                return self.userIdList
            return self.filterOutProtectedUsers()
        elif self.eventType == FILTER_HEICHAN_USER:
            if not self.isProtectedUser(self.userId):
                return self.userIdList
            return self.filterOutBlockedUsers()

    def filterOutProtectedUsers(self):
        userIdList = []
        for userId in self.userIdList:
            if userId == self.userId:
                userIdList.append(userId)
                continue

            userInfo = RoomServer.userCacheDao.loadUser(userId)
            # 过滤掉不存在的用户
            if not userInfo:
                continue

            # 不是受保护用户
            if not self.isProtectedUser(userId):
                userIdList.append(userId)
                continue

            # 受保护用户中，都在敏感省份的不做过滤
            isBlock, isSensitive = self.isBlockedUser(userId)
            if self.isSensitive and isSensitive:
                userIdList.append(userId)

        if ttlog.isDebugEnabled():
            ttlog.debug('BlackIndustryStrategy.filterOutProtectedUsers',
                        'userIds=', self.userIdList,
                        'after_filter=', userIdList)
        return userIdList

    # 将黑产用户从接受列表中去除
    def filterOutBlockedUsers(self):
        userIdList = []
        for userId in self.userIdList:
            isBlock, isSensitive = self.isBlockedUser(userId)
            # 不是黑产用户，不过滤
            if not isBlock:
                userIdList.append(userId)
                continue

            # 黑产用户中，如果都在敏感省份，不做过滤
            if self.isSensitive and isSensitive:
                userIdList.append(userId)

        if ttlog.isDebugEnabled():
            ttlog.debug('BlackIndustryStrategy.filterOutBlockedUsers',
                        'userIds=', self.userIdList,
                        'after_filter=', userIdList)
        return userIdList

    @staticmethod
    def isProtectedUser(userId):
        userInfo = RoomServer.userCacheDao.loadUser(userId)
        userDict = userInfo.toDict()
        registerTime = userDict.get('registerTime', 0)
        if time_utils.getCurrentTimestamp() - registerTime < 86400 * 3:
            return True
        return False

    @staticmethod
    @cachetools.func.ttl_cache(maxsize=5120, ttl=10)
    def isBlockedUser(userId):
        # 请求php-api获得是否是黑产用户
        code, resp = phpapi.queryUserInfoForRoom(userId)
        if code != 0:
            ttlog.error("phpapi.queryUserInfoForRoom",
                        'userId=', userId,
                        'code=', code,
                        'desc=', resp)
            return 0, 0
        return resp.get('isRestricter', 0), resp.get('isSensitiveAreas', 0)
