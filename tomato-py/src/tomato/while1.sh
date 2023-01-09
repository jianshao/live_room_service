#!/bin/bash
# Created on 2015-5-12
# @author: zqh


PYPY="${1}"
run="${2}"
serverId="${3}"
appModule="${4}"
configPath="${5}"
logsPath="${6}"
isReload="${7}"
args="${3} ${4} ${5} ${6} ${7}"

SENDMAIL=1
BIN_PATH="${BIN_PATH}"

script_outfile="${logsPath}/nohup.${3}"
echo "${serverId}" >> ${script_outfile}

function echomsg()
{
	msg=`date '+%F %T'`
	msg="${msg} ${1} ${2} ${3} ${4} ${5} ${6} ${7}"
	echo ${msg} >> ${script_outfile}
#	echo ${msg}
}


echomsg "Hook Script Log to :" "${script_outfile}"
echomsg "Hook Script argv :" "$@"
echomsg "Hook Script Start at :" "${run}"

while  [ 1 ]
do
	echomsg 'Hook Process Create.'
	echomsg "${PYPY} ${run} ${args}"
	${PYPY} ${run} ${args} >> ${script_outfile} 2>&1
	echomsg 'Hook Process Missing.'

	if [ ${SENDMAIL} -eq 1 ]
	then
	  mailparam="${serverId} "
      args="${serverId} ${appModule} ${configPath} ${logsPath} 1"
	  nohup ${PYPY} ${BIN_PATH}/remote.py sendmail crash ${mailparam} >> ${script_outfile} 2>&1 &
	else
		exit 1
	fi
done
