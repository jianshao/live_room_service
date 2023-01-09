# -*- coding=utf-8 -*-
'''
Created on 2017年11月20日

@author: zhaojiangang
'''
import codecs
from hashlib import md5
import json

import msgpack


def md5Digest(s, lower=True):
    '''
    计算一个字符串的MD5值O
    '''
    m = md5()
    m.update(s)
    ret = m.hexdigest()
    if lower:
        return ret.lower()
    return ret


def jsonLoads(jstr, encoding='utf8'):
    return json.loads(jstr, encoding=encoding)


def jsonLoadFile(filePath, encoding='utf8'):
    with codecs.open(filePath, 'r', encoding) as f:
        return json.load(f, encoding)


def jsonDumps(obj):
    return json.dumps(obj, separators=(',', ':'))


def msgpackLoads(obj, **kw):
    return msgpack.loads(obj, **kw)


def msgpackDumps(obj, **kw):
    return msgpack.dumps(obj, **kw)


