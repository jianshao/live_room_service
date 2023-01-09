# -*- coding=utf-8 -*-
'''
Created on 2019年11月9日

@author: laochao
'''
from tomato.core.lock import TTKeyLock


class MyClass(object):
    def __init__(self):
        self.userLock = TTKeyLock()

    def lock(self, userId):
        return self.userLock.lock(userId)


if __name__ == '__main__':
    my = MyClass()
    with my.lock(1):
        raise Exception()


