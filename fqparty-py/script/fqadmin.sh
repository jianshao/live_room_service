#!/bin/bash

SHELL_FOLDER=$(cd `dirname ${0}`; pwd)

export LOGDIR=./actlogs
# 先进入虚拟环境
cd /home/python/live_room_service && source venv/bin/activate
# 执行启动操作
pypy ${SHELL_FOLDER}/fqadmin.py "$@"
_RET_=$?
echo "=== fqadmin.sh done; status code: $_RET_ ==="
exit ${_RET_}

