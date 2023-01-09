# -*- coding:utf-8 -*-
'''
Created on 2020年10月26日

@author: zhaojiangang
'''
from fqparty import dao
from fqparty.dao.api.dao_api import UserDaoApi
from fqparty.dao.redis.dao_redis import RoomLocationDaoRedis, UserCacheDaoRedis, \
    SessionInfoDaoRedis, DaoRedis
from fqparty.domain.models.location import RoomLocationDao
from fqparty.domain.models.user import UserCacheDao, UserDao, SessionInfoDao
from fqparty.domain.services.user_service import UserService
from tomato.utils import ttlog


class UserServer(object):
    userDao = UserDao()
    userCacheDao = UserCacheDao()
    sessionInfoDao = SessionInfoDao()
    roomLocationDao = RoomLocationDao()
    
    userService = UserService()


def initServer():
    from fqparty.domain.services.impl.user_service_impl import UserServiceImpl
    
    userRedisDao = DaoRedis(dao.getRedisConns('users'))
    
    UserServer.userDao = UserDaoApi()
    UserServer.userCacheDao = UserCacheDaoRedis(userRedisDao)
    UserServer.sessionInfoDao = SessionInfoDaoRedis(userRedisDao)
    UserServer.roomLocationDao = RoomLocationDaoRedis(DaoRedis(dao.getRedisConns('common')))
    
    UserServer.userService = UserServiceImpl()
    ttlog.info('user.initServer')

def startServer():
    ttlog.info('user.startServer')


