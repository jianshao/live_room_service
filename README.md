语音平台房间内服务


1. 环境组装：
python版本：2.7
pypy版本：pypy2.7-v7.3.11-linux64.tar.gz
虚拟环境配置（使用对应用户执行命令）：
virtualenv -p /usr/bin/pypy venv #指定用/usr/bin/pypy做虚拟环境的解释器
source venv/bin/active  #载入虚拟环境
pypy get-pip.py  #如果get-pip.py过期，可以通过wget https://bootstrap.pypa.io/pip/2.7/get-pip.py下载
pypy -m pip install -r requirements.txt #使用虚拟环境依赖包组装环境


2. 服务启动/关闭
使用/home/match/fqgame/下的fqgame.sh脚本执行启动/关闭，update.sh执行代码/配置更新。
脚本执行日志在deploy/logs/nohup.*
fqgame.sh -h 查看帮助


3. 相关环境
测试环境：
线上环境：

4. 服务端口
http：
websocket：


5. 说明
服务上线使用的服务器需要与tomato/machines.conf配置中的强一致。
