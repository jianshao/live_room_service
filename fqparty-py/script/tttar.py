# -*- coding=utf-8 -*-
'''
Created on 2018年10月16日

@author: zhaojiangang
'''
import os
import shutil
import tarfile


def tar_cvfz(taroutbase, root_dir):
    root_dir = os.path.abspath(root_dir)
    lastname = root_dir.split(os.path.sep)[-1]
    root_dir = os.path.dirname(root_dir)
    base_dir = '.' + os.path.sep + lastname
    return shutil.make_archive(taroutbase, 'tar', root_dir, base_dir)


def tar_xvf(tarfilepath, out_dir):
    tar = tarfile.open(tarfilepath)
    names = tar.getnames()
    for name in names:
        tar.extract(name, path=out_dir)
    tar.close()


if __name__ == '__main__':
    print tar_cvfz('compile', './compile')

