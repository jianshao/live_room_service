# -*- coding=utf-8 -*-
'''
Created on 2014年7月10日

@author: zjgzzz@126.com
'''
import codecs
import os


class TTFileUtils(object):
    @classmethod
    def readTxtFile(cls, path, encoding='utf8'):
        f = codecs.open(path, 'r', encoding)
        try:
            return f.read()
        finally:
            if f:
                f.close()

    @classmethod
    def getFileSuffix(cls, path):
        start = path.rfind('/')
        start = start + 1 if start != -1 else 0
        index = path.rfind('.', start)
        if index == -1:
            return ''
        return path[index + 1:]
    
    @classmethod
    def isFileExists(cls, filepath):
        return os.path.isfile(filepath)


if __name__ == '__main__':
    assert('t' == TTFileUtils.getFileSuffix('/a/b/abc.t'))
    assert('' == TTFileUtils.getFileSuffix('/a/b/abc.'))
    assert('' == TTFileUtils.getFileSuffix('/a/b.b/abc'))


