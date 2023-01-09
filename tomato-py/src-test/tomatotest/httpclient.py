# -*- coding=utf-8 -*-
'''
Created on 2018年5月30日

@author: zhaojiangang
'''
from tomato.core import mainloop
from tomato.http.http import TTHttpClient
from tomato.utils import ttlog


wxInfo = {
       'appId':'wxb88f37292b790185',
       'secret':'7a6489b88078de16f146475779a933bd'
    }

def main():
    url = 'http://10.17.14.26:900/v1/account/loginBySnsId'
#     ttlog.setLevel(0)
    ttlog.setLevel(ttlog.INFO)
    ttlog.error('>>> before getJson')
    try:
        j = TTHttpClient.getJson(url, {}, params=None, timeout=10)
        ttlog.info('after getJson', j)
    except:
        ttlog.error('after getJson')
    finally:
        mainloop.stop()
#     mainloop.stop()


if __name__ == '__main__':
    mainloop.run(main)


