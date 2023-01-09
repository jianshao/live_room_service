# -*- coding=utf-8 -*-
'''
Created on 2018年10月16日

@author: zhaojiangang
'''
import os
import subprocess

import paramiko

import ttssh


def _dummy_file_callback(size, filesize):
    pass


_SSH_CLIENTS = {}


def closeAll():
    ips = _SSH_CLIENTS.keys()[:]
    for ip in ips:
        close(ip)

def close(ip):
    ssh = _SSH_CLIENTS.get(ip)
    if ssh:
        ssh.close()


class TTSSH(object):
    def __init__(self, ip, ssh, sftp):
        self._ip = ip
        self._ssh = ssh
        self._sftp = sftp
    
    @property
    def ip(self):
        return self._ip

    @property
    def sshClient(self):
        return self._ssh
    
    @property
    def sftpClient(self):
        return self._sftp

    def close(self):
        try:
            self._sftp.close()
        except:
            pass
        try:
            self._ssh.close();
        except:
            pass

    def exec_command(self, command, bufsize=-1,
        timeout=None, getPty=False, environment=None):
        _, stdouts_, stderrs_ = self._ssh.exec_command(command, bufsize=bufsize, timeout=timeout, get_pty=getPty, environment=environment)
        lines = []
        for line in stdouts_:
            lines.append(line.strip())
        
        for line in stderrs_:
            lines.append(line.strip())
        
        return lines
    
    def mkdirs(self, dirname):
        mpath = os.path.abspath(dirname)
        tks = mpath.split(os.path.sep)
        for x in xrange(len(tks) + 1) :
            p = os.path.sep.join(tks[0:x])
            if len(p) > 0 :
                try:
                    self._sftp.mkdir(p)
                except:
                    pass
        attr = self._sftp.stat(mpath)
        if attr.st_mtime <= 0 :
            raise Exception('Remote Folder make error ! ' + str(ip) + ':' + str(mpath))
    
    def put_file(self, localpath, remotepath, fun_callback=None):
        if not fun_callback:
            fun_callback = _dummy_file_callback
        attrs = self._sftp.put(localpath, remotepath, callback=fun_callback)
        return attrs.st_size


def _connect_with_key(ip, user, keyfile, password, port=22):
    key = paramiko.RSAKey.from_private_key_file(keyfile, password=password)
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.load_system_host_keys()
    s.connect(ip, port, username=user, pkey=key)
    return s


def _connect_with_password(ip, user, password, port=22):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(ip, port, user, password, timeout=15)
    return s


def _connect(options):
    keyfile = options.get('keyfile')
    if keyfile:
        return _connect_with_key(options['ip'], options['user'], keyfile, options.get('password'), options.get('port', 22))
    return _connect_with_password(options['ip'], options['user'], options.get('password'), options.get('port', 22))


def connect(options):
    sshClient = None
    sshFTP = None
    try:
        ssh = _SSH_CLIENTS.get(options['ip'])
        if ssh:
            return ssh
        sshClient = _connect(options)
        print 'sshClient=', sshClient
        sshFTP = sshClient.open_sftp()
        ssh = TTSSH(options['ip'], sshClient, sshFTP)
        _SSH_CLIENTS[options['ip']] = ssh
        return ssh
    except:
        if sshClient:
            sshClient.close()
        if sshFTP:
            sshFTP.close();
        raise

def execute_command_local(cmdline):
    print 'execute_command_local', ' '.join(cmdline)
    p = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    print p.communicate()[0]

def execute_command_remote(machine, cmdline):
    print 'execute_command_remote', machine['ip'], ' '.join(cmdline)
    ssh = ttssh.connect(machine)
    res = ssh.exec_command(' '.join(cmdline), getPty=False)
    print res
    
# #     child1 = psutil.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
#     psutil.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
# #     print p.communicate()[0]
# #     s1, s2 = p.communicate()
# #     outputs = s1 + '\n' + s2
# #     lines = outputs.split('\n')
# #     for x in xrange(len(lines)) :
# #         print lines[x]


if __name__ == '__main__':
    ip = '172.17.213.49'
    user = 'fanqiepy'
    keyfile = '/home/fanqiepy/.ssh/id_rsa'
    s = connect({
        'ip':ip,
        'user':user,
        'keyfile':keyfile
    })
    print 'ssh=', s
    print s.exec_command('ls', getPty=True)

#     
#     stdin, stdout, stderr = s.execCommand('sudo su - xingyue', getPty=True)
#     stdin.write('pwd' + '\n')
#     for line in stdout:
#         print line.strip('\n')
    
    print s.exec_command('ls', getPty=True)
    

