# -*- coding:utf-8 -*-
'''
Created on 2020年11月30日

@author: zhaojiangang
'''

import MySQLdb

def statics(userIds):
    exUserIds = set(userIds)
    while userIds:
        exUserIds.pop()
        
    for userId in exUserIds:
        
if __name__ == '__main__':
    pass