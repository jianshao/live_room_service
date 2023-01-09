# -*- coding:utf-8 -*-
'''
Created on 2020年12月22日

@author: zhaojiangang
'''
from sre_compile import isstring

from fqparty.domain.services.keyword_service import KeywordService
from tomato.http.http import TTHttpClient
from tomato.utils import ttlog, strutil


class KeywordServiceImpl(KeywordService):
    def __init__(self, url):
        self.url = url.encode('utf8')
    
    def filter(self, text):
        if not self.url:
            return text
        try:
            resp = TTHttpClient.getJson(self.url, {}, {'texts':strutil.jsonDumps([text])}, timeout=10, block=True)
            if ttlog.isDebugEnabled():
                ttlog.debug('KeywordServiceImpl.filter',
                            'url=', self.url,
                            'text=', text,
                            'resp=', resp)
                
            if not isinstance(resp, dict):
                ttlog.warn('KeywordServiceImpl.filter Failed',
                           'url=', self.url,
                           'text=', text,
                           'resp=', resp)
                return text
            ec = resp.get('code', 0)
            if ec != 0:
                ttlog.warn('KeywordServiceImpl.filter CodeFailed',
                           'url=', self.url,
                           'text=', text,
                           'resp=', resp)
                return text
            data = resp.get('data')
            if not isinstance(data, dict):
                ttlog.warn('KeywordServiceImpl.filter BadData',
                           'text=', text,
                           'resp=', resp)
                return text
            
            texts = data.get('texts')
            if not isinstance(texts, list) or len(texts) < 1:
                ttlog.warn('KeywordServiceImpl.filter BadTexts',
                           'url=', self.url,
                           
                           'text=', text,
                           'resp=', resp)
                return text
            
            if not isstring(texts[0]):
                ttlog.warn('KeywordServiceImpl.filter BadTextsData',
                           'url=', self.url,
                           'text=', text,
                           'resp=', resp)
                return text
            
            return texts[0]
        except:
            ttlog.error('KeywordServiceImpl.filter ServiceError',
                        'url=', self.url,
                        'text=', text)
            return text


