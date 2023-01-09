# -*- coding=utf-8 -*-
'''
Created on 2018年1月13日

@author: zhaojiangang
'''
from tomato.decorator.decorator import messageHandler


@messageHandler('/str/upper')
def strUpper(msg, sessionInfo):
    string = msg.body.get('string')
    return {'string':string.upper()}


