# -*- coding:utf-8 -*-
'''
Created on 2017年11月8日

@author: zhaojiangang
'''
from tomato.core.exceptions import TTException
from tomato.utils import ttlog


class TTConfable(object):
    TYPE_ID = 'unknown'

    def decodeFromDict(self, d):
        raise NotImplementedError
    

class TTClassRegister(object):
    '''
    类注册器
    '''
    _typeid_clz_map = {}

    @classmethod
    def findClass(cls, typeId):
        '''
        依据类型, 取得对应的注册的对象
        '''
        return cls._typeid_clz_map.get(typeId)

    @classmethod
    def unregisterClass(cls, typeId):
        '''
        删除一个typeId的注册对象
        '''
        return cls._typeid_clz_map.pop(typeId, None)

    @classmethod
    def registerClass(cls, typeId, clz):
        '''
        以typeId为关键字,注册对象clz
        注册的typeId不允许重复
        '''
        oldClz = cls.findClass(typeId)
        if oldClz:
            raise TypeError('%s already register %s for type %s' % (cls, oldClz, typeId))
        cls._typeid_clz_map[typeId] = clz


class TTConfableRegister(TTClassRegister):
    @classmethod
    def decodeFromDict(cls, d, *args, **kw):
        typeId = d.get('typeId')
        clz = cls.findClass(typeId)
        if not clz:
            raise TTException(-1, '%s unknown typeId %s' % (cls, typeId))
        
        try:
            confable = clz(*args, **kw)
            confable.decodeFromDict(d)
        except Exception, e:
            ttlog.error(clz, d)
            raise e
        return confable
    
    @classmethod
    def decodeList(cls, dictList, *args, **kw):
        ret = []
        for d in dictList:
            ret.append(cls.decodeFromDict(d, *args, **kw))
        return ret


