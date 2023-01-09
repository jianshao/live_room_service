# -*- coding=utf-8 -*-
'''
Created on 2016年10月21日

@author: zjgzzz@126.com
'''
import stackless

from tomato.core import reactor
from tomato.core.tasklet import TTTasklet


def stop():
    reactor.callLater(0, lambda: reactor.stop())

def run(main, *args, **kwargs):
    TTTasklet.createTasklet(main, *args, **kwargs)
    TTTasklet.createTasklet(reactor.run)
    stackless.run()


