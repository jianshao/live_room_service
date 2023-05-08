# -*- coding:utf-8 -*-
'''
Created on 2020年10月29日

@author: zhaojiangang
'''
import random
import traceback
import uuid

from tomato.utils import strutil


# map<uuid, set<md5> >
uuidMap = {}
def main(count):
    for _ in xrange(count):
        uuidstr = str(uuid.uuid1())
        md5list = uuidMap.get(uuidstr)
        if not md5list:
            md5list = set()
            uuidMap[uuidstr] = md5list
        md5str = strutil.md5Digest(uuidstr)
        md5list.add(md5str)
        if len(md5list) > 1:
            print('error')
        

def calc(price, gifts):
    values = [gift / float(price) for gift in gifts]
    valueSum = sum(values)
    print(values, valueSum)
    rets = [(1 - (float(v))) if v < 1 else float(v) / valueSum for v in values]
    sumRets = sum(rets)
    rets1 = [v / sumRets for v in rets]
    return rets, rets1, sum(rets)
    

def testString(keyword):
    d = {'key':keyword}
    keyword += 'haha'
    print(keyword)
    print(d['key'])

if __name__ == '__main__':
    try:
        keyword = 'hello'
        testString(keyword)
        s = unichr(11)
        print('unichr11=[%s]' % s, len(s))
        for w in keyword:
            print('[%s]' % (w))
#         price = 7
#         gifts = [1, 5, 8]
#         rets, rets1, total = calc(price, gifts)
#         print(rets, rets1, total
#         vs = [rets1[i] * 200 * gifts[i] for i in xrange(len(rets1))]
#         print(vs, sum(vs)
    except:
        traceback.print_exc()
        
    
    
    
    