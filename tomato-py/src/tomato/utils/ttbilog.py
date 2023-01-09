# -*- coding=utf-8 -*-
import cStringIO
import logging
import stackless
import sys
import traceback


FATAL = 60
ERROR = 50
WARN = 40
INFO = 30
DEBUG = 20
TRACE = 10
NOSET = 0

_levelToName = {
    FATAL:'F',
    ERROR:'E',
    WARN:'W',
    INFO:'I',
    DEBUG:'D',
    TRACE:'T',
    NOSET:'N'
}

_nameToLevel = {
    'F':FATAL,
    'E':ERROR,
    'W':WARN,
    'I':INFO,
    'D':DEBUG,
    'T':TRACE,
    'N':NOSET
}

def _formatTB(tb, limit=None):
    ret = []
    lines = traceback.format_tb(tb, limit)
    for line in lines:
        ret += line.split('\n')
    return ret

def _formatException(etype, value, tb, limit=None):
    """Format a stack trace and the exception information.

    The arguments have the same meaning as the corresponding arguments
    to print_exception().  The return value is a list of strings, each
    ending in a newline and some containing internal newlines.  When
    these lines are concatenated and printed, exactly the same text is
    printed as does print_exception().
    """
    if tb:
        ret = ['Traceback (most recent call last):']
        ret = ret + _formatTB(tb, limit)
    else:
        ret = []
    ret = ret + traceback.format_exception_only(etype, value)
    return ret


class _Formatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super(_Formatter, self).__init__(fmt, datefmt)
    
    def formatException(self, ei):
        """
        Format and return the specified exception information as a string.

        This default implementation just uses
        traceback.print_exception()
        """
        strs = ['E************************************************************']
        sio = cStringIO.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == '\n':
            s = s[:-1]
        strs.append(s)
        strs.append('E************************************************************')
        return '\n'.join(strs)


class TTLogger(object):
    def __init__(self, logger):
        self._logger = logger
        self._level = NOSET
    
    def addHandler(self, handler):
        '''
        添加logger处理器
        '''
        self._logger.addHandler(handler)
    
    def getLevel(self):
        '''
        获取日志级别
        '''
        return self._level
    
    def setLevel(self, level):
        '''
        设置日志级别
        '''
        self._level = level
    
    def getLevelName(self, level):
        '''
        获取级别名称
        '''
        return _levelToName.get(level, 'U')
    
    def isEnableFor(self, level):
        '''
        检查级别level是否开启
        '''
        return level >= self._level
    
    def log(self, level, *args, **kw):
        '''
        打印level级别的日志
        '''
        if self.isEnableFor(level):
            self._log(level, *args, **kw)
    
    def fatal(self, *args, **kw):
        '''
        打印FATAL级别的日志
        '''
        if self.isEnableFor(FATAL):
            self._log(FATAL, *args, **kw)
    
    def error(self, *args, **kw):
        '''
        打印ERROR级别的日志
        '''
        if self.isEnableFor(ERROR):
            self._log(ERROR, '************************************************************')
            self._log(ERROR, *args, **kw)
            try:
                etype, value, tb = sys.exc_info()
                lines = _formatException(etype, value, tb)
                for line in lines:
                    line = line.rstrip('\n')
                    if line:
                        self._log(ERROR, line, **kw)
            finally:
                etype = value = tb = None
            self._log(ERROR, '************************************************************')
    
    def warn(self, *args, **kw):
        '''
        打印WARN级别的日志
        '''
        if self.isEnableFor(WARN):
            self._log(WARN, *args, **kw)
    
    def info(self, *args, **kw):
        '''
        打印INFO级别的日志
        '''
        if self.isEnableFor(INFO):
            self._log(INFO, *args, **kw)
    
    def debug(self, *args, **kw):
        '''
        打印WARN级别的日志
        '''
        if self.isEnableFor(DEBUG):
            self._log(DEBUG, *args, **kw)
    
    def trace(self, *args, **kw):
        '''
        打印WARN级别的日志
        '''
        if self.isEnableFor(TRACE):
            self._log(TRACE, *args, **kw)
    
    def isDebugEnabled(self):
        '''
        检查DEBUG是否开启
        '''
        return self.isEnableFor(DEBUG)
    
    def isTraceEnabled(self):
        '''
        检查TRACE是否开启
        '''
        return self.isEnableFor(TRACE)
    
    def _log(self, level, *args, **kw):
        # 格式为 时间
        # task = stackless.getcurrent()
        # taskId = id(task) if task else 0
        # strs = ['%s %s' % (self.getLevelName(level), taskId)]
        strs = []
        for arg in args:
            if isinstance(arg, tuple):
                strs.append(str(arg))
            else:
                strs.append('%s' % (arg))
        msg = ' '.join(strs)
        self._logger.info(msg, **kw)


_loggerMap = {}

def _buildTomatoLogger():
    ch = logging.StreamHandler()                  # 定义console handler  
    formatter = _Formatter('%(asctime)s %(message)s')
    formatter.default_msec_format = '%s.%03d'
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    _l = logging.getLogger('tomato.bi')
    _l.setLevel(logging.DEBUG)
    _l.addHandler(ch)
    return TTLogger(_l)


# _loggerMap = {}
#['tomato'] = _buildTomatoLogger()


def createLogger(handler):
    _l = logging.getLogger('tomato.bi')
    _l.setLevel(logging.DEBUG)
    _l.addHandler(handler)
    _loggerMap['tomato.bi'] = TTLogger(_l)

def getLogger(name):
    '''
    获取
    '''
    l = _loggerMap.get(name)
    if not l:
        l = _buildTomatoLogger()
        _loggerMap[name] = l
    return l

def addHandler(handler):
    '''
    添加logger处理器
    '''
    getLogger('tomato.bi').addHandler(handler)
    
def getLevel():
    '''
    获取日志级别
    '''
    return getLogger('tomato.bi').getLevel()

def setLevel(level):
    '''
    设置日志级别
    '''
    getLogger('tomato.bi').setLevel(level)

def getLevelName(level):
    '''
    获取级别名称
    '''
    return getLogger('tomato.bi').getLevelName(level)

def isEnableFor(level):
    '''
    检查级别level是否开启
    '''
    return getLogger('tomato.bi').isEnableFor(level)

def log(level, *args, **kw):
    '''
    打印level级别的日志
    '''
    return getLogger('tomato.bi').log(level, *args, **kw)

def fatal(*args, **kw):
    '''
    打印FATAL级别的日志
    '''
    return getLogger('tomato.bi').fatal(*args, **kw)

def error(*args, **kw):
    '''
    打印ERROR级别的日志
    '''
    return getLogger('tomato.bi').error(*args, **kw)

def warn(*args, **kw):
    '''
    打印WARN级别的日志
    '''
    return getLogger('tomato.bi').warn(*args, **kw)

def info(*args, **kw):
    '''
    打印INFO级别的日志
    '''
    return getLogger('tomato.bi').info(*args, **kw)

def debug(*args, **kw):
    '''
    打印WARN级别的日志
    '''
    return getLogger('tomato.bi').debug(*args, **kw)

def trace(*args, **kw):
    '''
    打印WARN级别的日志
    '''
    return getLogger('tomato.bi').trace(*args, **kw)

def isDebugEnabled():
    '''
    检查DEBUG是否开启
    '''
    return getLogger('tomato.bi').isDebugEnabled()

def isTraceEnabled():
    '''
    检查TRACE是否开启
    '''
    return getLogger('tomato.bi').isTraceEnabled()


