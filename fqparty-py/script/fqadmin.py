# -*- coding=utf-8 -*-
'''
Created on 2018年10月12日

@author: zhaojiangang
'''
import codecs
import json
import os
import shutil

import ttadmin
from ttuitls import load_json_file, save_view_json_file


def check_config_file(filePath):
    try:
        with codecs.open(filePath, 'utf8') as f:
            json.load(f, 'utf8')
    except:
        raise

def ensue_dirs_and_save_json_file(filePath, data):
    try:
        os.makedirs(os.path.dirname(filePath))
    except OSError:
        pass
    save_view_json_file(filePath, data)


def load_matchines(config):
    '''
    获取所有机器配置
    '''
    ret = []
    configPath = config['configPath']
    machineMap = load_json_file(os.path.join(configPath, 'server/tomato/machines.json'))
    for name, m in machineMap.iteritems():
        m['name'] = name
        ret.append(m)
    return ret

def load_agents(config):
    '''
    加载所有agent配置
    '''
    configPath = config['configPath']
    return load_json_file(os.path.join(configPath, 'server/tomato/agents.json'))

def load_global(config):
    '''
    加载全局配置
    '''
    configPath = config['configPath']
    return load_json_file(os.path.join(configPath, 'server/fqparty/global.json'))

def gen_conn_servers(config, globalConf):
    '''
    生成所有长连接服务信息
    '''
    ret = []
    serverConf = globalConf.get('servers', {}).get('conn')
    if serverConf:
        prefix = globalConf.get('servers', {}).get('prefix')
        tcpPort = serverConf.get('tcpport', 0)
        wsPort = serverConf.get('wsport', 0)
        wsOldPort = serverConf.get('wsoldport', 0)
        if tcpPort or wsPort or wsOldPort:
            for i in xrange(serverConf['count']):
                listenings = {}
                if tcpPort:
                    listenings['tcp'] = {'port':tcpPort}
                    tcpPort += 1
                if wsPort:
                    listenings['ws'] = {'port':wsPort}
                    wsPort += 1
                if wsOldPort: 
                    listenings['wsold'] = {'port':wsOldPort}
                    wsOldPort += 1
                serverNo = i + 1
                ret.append({
                    'serverId': '%s_CO%06d' % (prefix, serverNo),
                    'frontend':{
                        'maxConnection': serverConf['maxConnection'],
                        'listenings':listenings
                    }
                })
    return ret

def gen_http_servers(config, globalConf):
    ret = []
    serverConf = globalConf.get('servers', {}).get('http')
    if serverConf:
        prefix = globalConf.get('servers', {}).get('prefix')
        port = serverConf.get('port', 0)
        assert(port > 0)
        for i in xrange(serverConf['count']):
            serverNo = i + 1
            ret.append({
                'serverId':'%s_HT%06d' % (prefix, serverNo),
                'http':{
                    'port':port + i
                }
            })
    return ret

def gen_user_servers(config, globalConf):
    ret = []
    serverConf = globalConf.get('servers', {}).get('user')
    if serverConf:
        prefix = globalConf.get('servers', {}).get('prefix')
        for i in xrange(serverConf['count']):
            serverNo = i + 1
            ret.append({
                'serverId':'%s_US%06d' % (prefix, serverNo)
            })
    return ret

def gen_room_servers(config, globalConf):
    ret = []
    serverConf = globalConf.get('servers', {}).get('room')
    if serverConf:
        prefix = globalConf.get('servers', {}).get('prefix')
        for i in xrange(serverConf['count']):
            serverNo = i + 1
            ret.append({
                'serverId':'%s_RM%06d' % (prefix, serverNo)
            })
    return ret

def gen_mic_servers(config, globalConf):
    ret = []
    serverConf = globalConf.get('servers', {}).get('mic')
    if serverConf:
        prefix = globalConf.get('servers', {}).get('prefix')
        for i in xrange(serverConf['count']):
            serverNo = i + 1
            ret.append({
                'serverId':'%s_MC%06d' % (prefix, serverNo)
            })
    return ret

def gen_servers(config):
    '''
    生成所有server配置
    '''
#     CONN = 'conn'
#     HTTP = 'http'
#     USER = 'user'
#     ROOM = 'room'

    ret = {}
    globalConf = load_global(config)
    
    # 长连接
    ret['conn'] = gen_conn_servers(config, globalConf)
    ret['http'] = gen_http_servers(config, globalConf)
    ret['room'] = gen_room_servers(config, globalConf)
    ret['mic'] = gen_mic_servers(config, globalConf)
    ret['user'] = gen_user_servers(config, globalConf)

    return ret

def distribution_servers(config, typedServers):
    machineIndex = 0
    agentIndex = 0
    machines = sorted(load_matchines(config), key=lambda m:m['name'])
    print('machines=', machines)
    agents = load_agents(config)
    
    # conn 和http优先处理，主要是nginx转发需要配置
    connServers = typedServers['conn']
    
    for serverInfo in connServers:
        m = machines[machineIndex]
        agent = agents[agentIndex]
        machineIndex = (machineIndex + 1) % len(machines)
        agentIndex = (agentIndex + 1) % len(agents)
        serverInfo['machine'] = m['name']
        serverInfo['agentId'] = agent['agentId']
    
    machineIndex = 0
    httpServers = typedServers['http']
    for serverInfo in httpServers:
        m = machines[machineIndex]
        agent = agents[agentIndex]
        machineIndex = (machineIndex + 1) % len(machines)
        agentIndex = (agentIndex + 1) % len(agents)
        serverInfo['machine'] = m['name']
        serverInfo['agentId'] = agent['agentId'] 
        
    machineIndex = 0
    for serverType, typeServers in typedServers.iteritems():
        if serverType in ['conn', 'http']:
            continue
        for serverInfo in typeServers:
            m = machines[machineIndex]
            agent = agents[agentIndex]
            machineIndex = (machineIndex + 1) % len(machines)
            agentIndex = (agentIndex + 1) % len(agents)
            serverInfo['machine'] = m['name']
            serverInfo['agentId'] = agent['agentId']


def make_config(config):
    '''
    生成配置，只生成server目录下的文件
    '''
    
    servers = gen_servers(config)
    distribution_servers(config, servers)
    
    # 生成目录
    compileConfigPath = os.path.join(config['compilePath'], 'config')
    if os.path.isdir(compileConfigPath):
        shutil.rmtree(compileConfigPath)
    os.mkdir(compileConfigPath)
    
    configPath = config['configPath']
    dirs = ['server']
    
    # 拷贝目录中所有文件到deployConfPath
    while dirs:
        # 遍历目录
        d = dirs.pop(0)
        for name in os.listdir(os.path.join(configPath, d)):
            sf = os.path.join(d, name)
            if os.path.isdir(os.path.join(configPath, sf)):
                dirs.append(sf)
            elif os.path.isfile(os.path.join(configPath, sf)):
                if sf.endswith('.json'):
                    sdFullPath = os.path.join(configPath, sf)
                    # 检查是否是合法的json
                    data = load_json_file(sdFullPath)
                    wfile = os.path.join(compileConfigPath, sf)
                    ensue_dirs_and_save_json_file(wfile, data)
#                     
#                     # 生成写入redis的命令
#                     key = sf.replace(os.path.sep, '.')[0:-5]
#                     kvs[key] = load_json_file(sdFullPath)
    
    serversPath = os.path.join(compileConfigPath, 'server/tomato/servers.json')
    ensue_dirs_and_save_json_file(serversPath, servers)
    

def main():
    ttadmin.make_config = make_config
    ttadmin.server_types_sort = ['user', 'room', 'http', 'conn']
    ttadmin.main()

if __name__ == '__main__':
    main()
    

