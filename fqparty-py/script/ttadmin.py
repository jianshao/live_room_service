#!/usr/bin/python
# -*- coding=utf-8 -*-
'''
Created on 2018年10月14日

@author: zhaojiangang
'''

import argparse
import compileall
from datetime import datetime
import os
import shutil
import sys
import requests

import ttssh
from tttar import tar_xvf
import tttar
from ttuitls import load_json_file, get_local_machine_ips, ensure_dir_exists

usage = """
         fqadmin.sh -c <config path> command

支持的命令:
         fqadmin.sh -c <config path> start            启动所有服务进程
                                                      --reload 0 不加载缓存数据到内存；1 加载缓存数据到内存

         fqadmin.sh -c <config path> stop             停止所有服务进程
         fqadmin.sh -c <config path> update_config    重新加载配置文件
"""


def copy_sources(config):
    # 删除bin目录下所有目录
    compileBinPath = os.path.join(config['compilePath'], 'bin')

    print 'copy_sources', compileBinPath

    if os.path.isdir(compileBinPath):
        shutil.rmtree(compileBinPath)
    os.mkdir(compileBinPath)

    for project in config['projects']:
        for source in project.get('sources', []):
            src = os.path.join(config['projectsPath'], project['path'], source)
            for name in os.listdir(src):
                s = os.path.join(src, name)
                d = os.path.join(compileBinPath, name)
                if os.path.isdir(s):
                    shutil.copytree(s, d)


def compile_sources(config):
    compileBinPath = os.path.join(config['compilePath'], 'bin')

    print 'compile_sources', compileBinPath

    compileall.compile_dir(compileBinPath, quiet=1)
    dirs = [compileBinPath]

    while dirs:
        d = dirs.pop(0)
        for name in os.listdir(d):
            sd = os.path.join(d, name)
            if os.path.isdir(sd):
                dirs.append(sd)
            elif os.path.isfile(sd):
                if sd.endswith('.pyc'):
                    os.remove(sd)


def do_command_compile(commandCtx):
    # 拷贝源代码
    print 'do_command_compile', commandCtx.args
    copy_sources(commandCtx.config)
    compile_sources(commandCtx.config)


def make_config(config):
    '''
    '''
    pass


def put_config_to_all_machine(commandCtx):
    '''
    奖所有配置写入redis
    '''
    print 'put_config_to_all_machine', commandCtx.args
    machinesFilePath = os.path.join(commandCtx.config['configPath'], 'server/tomato/machines.json')
    machines = load_json_file(machinesFilePath)

    fileName = 'config_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    compileConfigPath = os.path.join(commandCtx.config['compilePath'], 'config')
    outPath = os.path.join(commandCtx.config['backPath'], fileName)
    if not os.path.isdir(commandCtx.config['backPath']):
        os.mkdir(commandCtx.config['backPath'])

    tarFile = tttar.tar_cvfz(outPath, compileConfigPath)

    print 'tarFile=', tarFile

    for machine in machines.values():
        put_tar_to_machine(commandCtx, machine, tarFile)

    print 'put config finished'


def do_command_config_compile(commandCtx):
    '''
    '''
    print 'do_command_config_compile', commandCtx.args
    # 生成
    make_config(commandCtx.config)


def do_command_config_update(commandCtx):
    '''
    '''
    print 'do_command_config_update', commandCtx.args
    # 生成
    put_config_to_all_machine(commandCtx)


def put_tar_to_machine(commandCtx, machine, tarFile):
    print 'put_tar_to_machine', commandCtx.args, machine, sys.argv[0]

    deployPath = os.path.join(commandCtx.config['deployPath'])

    backPath = os.path.join(deployPath, 'back')
    logsPath = os.path.join(deployPath, 'logs')
    scriptPath = os.path.join(deployPath, 'script')
    remoteFile = os.path.join(os.path.dirname(sys.argv[0]), 'remote.py')
    remoteFileDest = os.path.join(scriptPath, 'remote.py')

    if machine['ip'] in commandCtx.localIps:
        # 本机
        print 'put_code_to_machine to local', tarFile
        ensure_dir_exists(backPath)
        ensure_dir_exists(logsPath)
        ensure_dir_exists(scriptPath)
        tar_xvf(tarFile, deployPath)
        shutil.copy(remoteFile, remoteFileDest)
        return

    print 'put_code_to_machine to remote', machine['ip']

    ssh = ttssh.connect(machine)

    # 创建目录
    ssh.mkdirs(backPath)
    ssh.mkdirs(logsPath)
    ssh.mkdirs(scriptPath)

    # 上传remote
    ssh.put_file(remoteFile, remoteFileDest)
    print 'put_file', remoteFile, remoteFileDest, 'ok'

    localfilesize = os.path.getsize(tarFile)

    # 打包
    def update_send_size(sendsize_, allsize_):
        if sendsize_ == allsize_:
            p = 100
        else:
            p = int((float(sendsize_) / float(allsize_)) * 100)

        percent = '%03d' % (p) + '%'
        print 'percent ', percent

    remoteTarFile = os.path.join(backPath, os.path.basename(tarFile))

    print 'put_code_to_machine to remote', machine['ip'], tarFile, remoteTarFile

    putsize = ssh.put_file(tarFile, remoteTarFile, update_send_size)

    if int(putsize) != localfilesize:
        return 2, 'SSH Push ERROR ' + tarFile

    cmd = '%s %s xvf %s %s %s %s' % (commandCtx.config['pypy'], remoteFileDest, remoteTarFile, deployPath, 'bin', 1)
    print 'exec remote command: ', cmd
    lines = ssh.exec_command(cmd)
    print lines
    return 0, None


def put_code_to_all_machine(commandCtx):
    '''
    推送代码到所有机器
    '''
    print 'put_code_to_all_machine', commandCtx.args
    machinesFilePath = os.path.join(commandCtx.config['configPath'], 'server/tomato/machines.json')
    machines = load_json_file(machinesFilePath)

    fileName = 'bin_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    compileBinPath = os.path.join(commandCtx.config['compilePath'], 'bin')
    outPath = os.path.join(commandCtx.config['backPath'], fileName)
    if not os.path.isdir(commandCtx.config['backPath']):
        os.mkdir(commandCtx.config['backPath'])

    tarFile = tttar.tar_cvfz(outPath, compileBinPath)

    print 'tarFile=', tarFile
    for machine in machines.values():
        put_tar_to_machine(commandCtx, machine, tarFile)

    print 'put code finished'


def do_command_put_code(commandCtx):
    # 拷贝源代码
    print 'do_command_put_code', commandCtx.args
    # 上传代码到所有机器
    put_code_to_all_machine(commandCtx)


def load_deploy_servers_config(config):
    return load_json_file(os.path.join(config['deployPath'], 'config/server/tomato/servers.json'))


def load_compile_matchines(config):
    '''
    获取所有机器配置
    '''
    ret = []
    configPath = os.path.join(config['compilePath'], 'config')
    machineMap = load_json_file(os.path.join(configPath, 'server/tomato/machines.json'))
    for name, m in machineMap.iteritems():
        m['name'] = name
        ret.append(m)
    return ret


server_types_sort = []


def sortServerType(serverType, serverTypeCount):
    try:
        return server_types_sort.index(serverType)
    except ValueError:
        return serverTypeCount


def start_processes(commandCtx, machine, servers):
    config = commandCtx.config

    remotePy = os.path.join(config['deployPath'], 'script/remote.py')

    #     remote.py start <pypy> <deployPath> <appModule> <redisConf> [serverIds...]'
    #     cmd = 'python %s start %s %s %s %s' % (remotePy, config['pypy'],
    #                                            config['deployPath'], config['appModule'],
    #                                            os.path.join(config['deployPath'], 'config'))

    cmdline = ['python', remotePy, 'start', config['pypy'], config['deployPath'], config['appModule'],
               os.path.join(config['deployPath'], 'config'), commandCtx.args.reload]
    for server in servers:
        cmdline.append(server['serverId'])

    if machine['ip'] in commandCtx.localIps:
        # 本机
        print 'run local cmd', ' '.join(cmdline)
        ttssh.execute_command_local(cmdline)
    else:
        print 'run remote cmd', machine['ip'], ' '.join(cmdline)
        ttssh.execute_command_remote(machine, cmdline)


def start_all_processes(commandCtx):
    '''
    启动所有进程
    '''
    print 'start_all_processes', commandCtx.args
    # 获取排序规则
    if commandCtx.args.sort:
        print 'start_all_processes sort'

    # 读取servers.json
    typedServerMap = load_deploy_servers_config(commandCtx.config)

    # 最后启动conn
    serverTypes = sorted(typedServerMap.keys(), key=lambda serverType: sortServerType(serverType, len(typedServerMap)))

    print serverTypes

    machines = load_compile_matchines(commandCtx.config)
    machineMap = {m['name']: m for m in machines}
    # 根据配置中的serverIds启动所有服务器进程
    for serverType in serverTypes:
        # 根据进程所在机器收集
        machineProcessMap = {}
        for server in typedServerMap[serverType]:
            machineServers = machineProcessMap.get(server['machine'])
            if not machineServers:
                machineServers = []
                machineProcessMap[server['machine']] = machineServers
            machineServers.append(server)

        for mname, servers in machineProcessMap.iteritems():
            machine = machineMap.get(mname)
            start_processes(commandCtx, machine, servers)


def do_command_start(commandCtx):
    print 'do_command_start', commandCtx.args
    make_config(commandCtx.config)
    copy_sources(commandCtx.config)
    compile_sources(commandCtx.config)

    put_config_to_all_machine(commandCtx)
    put_code_to_all_machine(commandCtx)

    start_all_processes(commandCtx)


def stop_processes(commandCtx, machine, servers):
    config = commandCtx.config

    remotePy = os.path.join(config['deployPath'], 'script/remote.py')

    #     remote.py start <pypy> <deployPath> <appModule> <redisConf> [serverIds...]'
    #     cmd = 'python %s stop %s %s %s %s' % (remotePy, config['pypy'],
    #                                            config['deployPath'], config['appModule'],
    #                                            os.path.join(config['deployPath'], 'config'))
    #
    cmdline = ['python', remotePy, 'stop', config['pypy'], config['deployPath'], config['appModule'],
               os.path.join(config['deployPath'], 'config'), commandCtx.args.reload]

    for server in servers:
        cmdline.append(server['serverId'])

    if machine['ip'] in commandCtx.localIps:
        # 本机
        print 'run local cmd', ' '.join(cmdline)
        ttssh.execute_command_local(cmdline)
    else:
        print 'run remote cmd', machine['ip'], ' '.join(cmdline)
        ttssh.execute_command_remote(machine, cmdline)


def stop_all_processes(commandCtx):
    machines = load_compile_matchines(commandCtx.config)
    machineMap = {m['name']: m for m in machines}

    # 获取所有进程的信息
    typedServerMap = load_deploy_servers_config(commandCtx.config)
    serverTypes = sorted(typedServerMap.keys(), key=lambda serverType: sortServerType(serverType, len(typedServerMap)),
                         reverse=True)

    # 根据配置中的serverIds启动所有服务器进程
    for serverType in serverTypes:
        # 根据进程所在机器收集
        machineProcessMap = {}
        for server in typedServerMap[serverType]:
            machineServers = machineProcessMap.get(server['machine'])
            if not machineServers:
                machineServers = []
                machineProcessMap[server['machine']] = machineServers
            machineServers.append(server)

        for mname, servers in machineProcessMap.iteritems():
            machine = machineMap.get(mname)
            stop_processes(commandCtx, machine, servers)


def do_command_stop(commandCtx):
    print 'do_command_stop', commandCtx.args
    stop_all_processes(commandCtx)


def get_server_ids(config):
    server_ids = []
    servers_file = os.path.join(config['deployPath'], 'config/server/tomato/servers.json')
    servers = load_json_file(servers_file)
    for server_infos in servers.values():
        for server_info in server_infos:
            server_ids.append(server_info['serverId'])
    return ','.join(server_ids)


def do_update_config(command_ctx):
    server_ids = get_server_ids(command_ctx.config)
    http_url = command_ctx.config.get('http_url')
    http_url = http_url + "/iapi/reloadConfig"
    params = {
        'serverIds': server_ids,
    }

    print "serverIds   =", server_ids
    print "http_url   =", http_url
    print "params     =", params

    result = requests.get(http_url, params=params)
    print 'result    =', result.text


def do_command_update_config(command_ctx):
    print 'do_command_update_config'
    make_config(command_ctx.config)
    put_config_to_all_machine(command_ctx)
    do_update_config(command_ctx)


command_map = {
    'compile': do_command_compile,
    'put_code': do_command_put_code,
    'start': do_command_start,
    'stop': do_command_stop,
    'update_config': do_command_update_config
}


def run_command(commandCtx, extCommandMap):
    handler = None
    if extCommandMap:
        handler = extCommandMap.get(commandCtx.command)
    if not handler:
        handler = command_map.get(commandCtx.command)
        if not handler:
            raise Exception('Unknown command %s' % (commandCtx.command))
    handler(commandCtx)


class CommandContext(object):
    def __init__(self, args):
        self.args = args
        self.command = args.command
        self.config = load_json_file(args.config)
        self.localIps = get_local_machine_ips()


def main(extCommandMap=None):
    argparser = argparse.ArgumentParser(add_help=False, usage=usage)
    argparser.add_argument('command', help='要执行的命令', type=str)
    argparser.add_argument('-h', '--help', action='help',
                           default=argparse.SUPPRESS,
                           help='显示帮助信息')
    argparser.add_argument('-c', '--config', help='指定配置文件路径', dest='config', type=str)
    argparser.add_argument('-s', '--sort', help='指定进程启动顺序排序规则servertype1:servertype2', dest='sort', type=str)
    argparser.add_argument('--reload', help='加载缓存', dest='reload', type=str, default='0')
    args = argparser.parse_args()
    run_command(CommandContext(args), extCommandMap)


if __name__ == '__main__':
    main()
