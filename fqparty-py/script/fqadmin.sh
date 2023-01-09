#!/bin/bash

SHELL_FOLDER=$(cd `dirname ${0}`; pwd)

export LOGDIR=./actlogs
pypy ${SHELL_FOLDER}/fqadmin.py "$@"
_RET_=$?
echo "=== fqadmin.sh done; status code: $_RET_ ==="
exit ${_RET_}

