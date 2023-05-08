# -*- coding=utf-8 -*-
'''
Created on 2018年10月11日

@author: zhaojiangang
'''
import codecs
import json
import os
import platform
import re
import subprocess


def load_json_file(filePath, encoding='utf8'):
    print('load_json_file', filePath)
    with codecs.open(filePath, 'r', encoding) as f:
        return json.load(f)


def save_json_file(filePath, data, encoding='utf8'):
    with codecs.open(filePath, 'w', encoding) as f:
        json.dump(data, f, separators=(',', ':'))

def save_view_json_file(filePath, data, encoding='utf8'):
    with codecs.open(filePath, 'w', encoding) as f:
        json.dump(data, f, indent=4)


def save_file(filePath, data, encoding='utf8'):
    with codecs.open(filePath, 'w', encoding) as f:
        f.write(data)


def ensure_dir_exists(dirPath):
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)
        
        
def get_local_machine_ips():
    # LINUX MAC WIN32
    iplist = []
    curplatform = platform.system()
    ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
    if curplatform == 'Darwin' or curplatform == 'Linux':
        ipconfig_process = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile('(inet %s)' % ipstr)
        pattern = re.compile(ipstr)
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            iplist.append(ip.group())
    elif curplatform == 'Windows':
        ipconfig_process = subprocess.Popen('ipconfig', stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile('IPv4.*: %s' % ipstr)
        pattern = re.compile(ipstr)
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            iplist.append(ip.group())
    
    if not iplist:
        iplist.append('127.0.0.1')
    print('get_local_machine_ips system=', curplatform, 'iplist=', iplist)
    return iplist


if __name__ == '__main__':
    get_local_machine_ips()
    