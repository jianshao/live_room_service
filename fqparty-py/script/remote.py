# -*- coding=utf-8 -*-
'''
Created on 2018年10月17日

@author: zhaojiangang
'''
import socket
import argparse
import commands
import getpass
import os
import subprocess
import traceback
import requests

import psutil


def parse_str_redis_conf(redisConf):
    parts = redisConf.split(':')
    if len(parts) == 0:
        return parts
    return parts[0], int(parts[1]), int(parts[2])


def _popen_process_while1(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverId):
    '''
    启动所有的while1进程
    '''
    run = '%s/bin/tomato/run.py' % (deployPath)
    while1 = '%s/bin/tomato/while1.sh' % (deployPath)
    logsPath = '%s/logs' % (deployPath)
    os.environ["BIN_PATH"] = os.path.join(deployPath, 'script')

    env = dict(os.environ)
    pythonPath = env.get('PYTHONPATH', '')
    pythonPath += ':%s' % (os.path.join(deployPath, 'bin'))
    env['PYTHONPATH'] = pythonPath
    os.chmod(while1, 00777)
    cmd = '%s %s %s %s %s %s %s %s' % (
        while1, pypy, run, serverId, appModule, configPathOrConfigRedis, logsPath, isReload)
    print '>>> run cmd %s' % (cmd)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, env=env)


def start_server(pypy, deployPath, appModule, configPathOrConfigRedis, serverId):
    '''
    启动server
    '''
    run = '%s/bin/tomato/run.py' % (deployPath)
    logsPath = '%s/logs' % (deployPath)
    env = dict(os.environ)
    pythonPath = env.get('PYTHONPATH', '')
    pythonPath += ':%s' % (os.path.join(deployPath, 'bin'))
    env['PYTHONPATH'] = pythonPath
    cmd = 'nohup %s %s %s %s %s %s' % (pypy, run, serverId, appModule, configPathOrConfigRedis, logsPath)
    print '>>> run cmd %s' % (cmd)
    subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, env=env)


def start_servers(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverIds):
    '''
    启动给定的所有serverId
    '''
    for serverId in serverIds:
        _popen_process_while1(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverId)


def get_pids(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverIds):
    curUser = getpass.getuser()
    sidplist = []

    for p in psutil.process_iter():
        try:
            if p.username() == curUser:
                cmdline = p.cmdline()
                cmdline = ' '.join(cmdline)
                for serverId in serverIds:
                    run = '%s/bin/tomato/run.py' % (deployPath)
                    logsPath = '%s/logs' % (deployPath)
                    cmd = '%s %s %s %s %s %s 1' % (pypy, run, serverId, appModule, configPathOrConfigRedis, logsPath)
                    if cmdline.find(cmd) != -1:
                        sidplist.append((serverId, p))
                    cmd = '%s %s %s %s %s %s 0' % (pypy, run, serverId, appModule, configPathOrConfigRedis, logsPath)
                    if cmdline.find(cmd) != -1:
                        sidplist.append((serverId, p))
            else:
                continue
        except:
            continue

    return sidplist


def stop_servers(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverIds):
    print 'stop servers', serverIds
    pids = get_pids(pypy, deployPath, appModule, configPathOrConfigRedis, isReload, serverIds)
    for serverId, p in pids:
        try:
            print 'kill pid', serverId, p.pid
            p.kill()
        except:
            traceback.print_exc()


def find_sub_files(fpath):
    ffiles = set()
    fpath = os.path.abspath(fpath)
    for p, _, filenames in os.walk(fpath):
        for filename in filenames:
            filename = os.path.join(p, filename)
            filename = os.path.abspath(filename)
            ffiles.add(filename)
    return ffiles


def tar_xvf(tarfilepath, out_dir, sub_dir, rmLeft):
    import tarfile
    tar = tarfile.open(tarfilepath)
    print('tar_xvf->', tarfilepath, out_dir)
    names = tar.getnames()
    newfiles = set()
    for name in names:
        newf = tar.extractfile(name)
        if newf:
            newdata = newf.read()
            newf.close()
            oldf = None
            olddata = None
            outfile = os.path.join(out_dir, name)
            outfile = os.path.abspath(outfile)
            try:
                oldf = open(outfile, 'r')
                olddata = oldf.read()
            except:
                try:
                    oldf.close()
                except:
                    pass
            newfiles.add(outfile)
            newfiles.add(outfile + 'c')
            if olddata != newdata:
                outf = open(outfile, 'w')
                outf.write(newdata)
                outf.close()
        else:
            tar.extract(name, path=out_dir)
    tar.close()
    if int(rmLeft):
        subfiles = find_sub_files(os.path.join(out_dir, sub_dir))
        delfiles = list(subfiles - newfiles)
        delfiles.sort()
        for df in delfiles:
            commands.getoutput('rm -fr ' + df)
    print('tar_xvf->', tarfilepath, out_dir, 'done.')


def do_command_xvf(*args):
    print 'do_command_xvf', args
    if len(args) < 4:
        print args
        print 'remote.py xvf <tarfilepath> <out_dir> <sub_dir> <rmLeft>'
        exit(-1)
    tar_xvf(args[0], args[1], args[2], args[3])


def do_command_start_servers(*args):
    #     pypy, deployPath, appModule, redisConf, serverIds
    if len(args) < 5:
        print args
        print 'remote.py start <pypy> <deployPath> <appModule> <configPath> [serverIds...]'
        exit(-1)
    pypy = args[0]
    deployPath = args[1]
    appModule = args[2]
    configPath = args[3]
    isReload = args[4]
    serverIds = args[5:]

    print 'do_command_start_servers', args
    start_servers(pypy, deployPath, appModule, configPath, isReload, serverIds)


def do_command_stop_servers(*args):
    if len(args) < 5:
        print args
        print 'remote.py stop <pypy> <deployPath> <appModule> <configPath> [serverIds...]'
        exit(-1)
    pypy = args[0]
    deployPath = args[1]
    appModule = args[2]
    configPath = args[3]
    isReload = args[4]
    serverIds = args[5:]

    print 'do_command_stop_servers'

    stop_servers(pypy, deployPath, appModule, configPath, isReload, serverIds)


def do_command_sendmail(*args):
    env = os.environ.get('ENV', 'prod')
    if env != 'prod':
        return

    server_id = args[1]
    url = 'https://oapi.dingtalk.com/robot/send'
    token = '2b3fd944d70ad573b435f35a9f02f45993f4b4d8cd0e60f029e092e102afcc69'

    params = {
        'access_token': token,
    }
    data = {
        "msgtype": "text",
        "text": {
            "content": "【报警】 pypy进程异常退出  host: %s  server_id: %s" % (socket.gethostname(), server_id)
        }
    }

    resp = requests.post(url, params=params, json=data)
    if resp.status_code == 200:
        print(resp.json())
    else:
        print(resp.text)


command_map = {
    'xvf': do_command_xvf,
    'start': do_command_start_servers,
    'stop': do_command_stop_servers,
    'sendmail': do_command_sendmail
}


def run_command(args):
    handler = command_map.get(args.command)
    if handler:
        if args.args:
            handler(*args.args)
        else:
            handler()


def main():
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('command', help='要执行的命令', type=str)
    argparser.add_argument('args', help='要执行的命令', type=str, nargs='*')
    argparser.add_argument('-h', '--help', action='help',
                           default=argparse.SUPPRESS,
                           help='显示帮助信息')
    args = argparser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
