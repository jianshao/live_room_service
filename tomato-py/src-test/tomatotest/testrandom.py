# -*- coding:utf-8 -*-
'''
Created on 2020年11月26日

@author: zhaojiangang
'''
import random


giftsConf = [
    {"giftId":"387","weight":2},
    {"giftId":"388","weight":8},
    {"giftId":"405","weight":29},
    {"giftId":"390","weight":50},
    {"giftId":"385","weight":1},
    {"giftId":"407","weight":1},
    {"giftId":"389","weight":705},
    {"giftId":"397","weight":1800},
    {"giftId":"400","weight":10000},
    {"giftId":"402","weight":11000},
    {"giftId":"404","weight":88888},
    {"giftId":"396","weight":98888},
]


def random1(gifts):
    totalWeight = 0
    giftWeightList = []
    for gift in gifts:
        totalWeight += gift['weight']
        giftWeightList.append((gift, totalWeight))
    
    r = random.randint(1, totalWeight)
    for gift, weight in giftWeightList:
        if r <= weight:
            return gift

    return None


def random2(gifts):
    totalWeight = 0
    for gift in gifts:
        totalWeight += gift['weight']
    
    sortedGifts = sorted(gifts, key=lambda x:x['weight'])
    for gift in sortedGifts:
        r = random.randint(1, totalWeight)
        if r <= gift['weight']:
            return gift
        totalWeight -= gift['weight']

    return None

def test(randomFunc, gifts, count):
    ret = {}
    for _ in xrange(count):
        gift = randomFunc(gifts)
        v = ret.get(gift['giftId'])
        if not v:
            ret[gift['giftId']] = (gift, 1)
        else:
            ret[gift['giftId']] = (gift, v[1] + 1)
    return ret.values()


if __name__ == '__main__':
    count = 800000
    totalWeight = sum([gift['weight'] for gift in giftsConf])
    for _ in xrange(1):
        res = test(random2, giftsConf, count)
        sortedRes = sorted(res, key=lambda giftV: (giftV[0]['weight'], giftV[0]['giftId']))
        print 'new', [(v[0]['giftId'], v[1], '%.5f%%' % (float(v[0]['weight']) / totalWeight * 100), '%.5f%%' % (float(v[1]) / count * 100)) for v in sortedRes]
    for _ in xrange(1):
        res = test(random1, giftsConf, count)
        sortedRes = sorted(res, key=lambda giftV: (giftV[0]['weight'], giftV[0]['giftId']))
        print 'old', [(v[0]['giftId'], v[1], '%.5f%%' % (float(v[0]['weight']) / totalWeight * 100), '%.5f%%' % (float(v[1]) / count * 100)) for v in sortedRes]


