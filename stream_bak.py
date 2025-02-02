# coding: utf-8
import ffmpeg
import os
import sys
import random
import time
from datetime import datetime
import shutil
from queue import Queue
import threading
import shell as shell
import class_subtitle as class_subtitle
import class_voice as class_voice

# timer = threading.Timer(5, func,(1,))
# time0 = time.time()
# timer.start()

MAX_MEMORY = 100
BAK_MP4_PATH = 's365_432p_201_192k.mp4'
# Error writing trailer of rtmp://live-push.bilivideo.com/live-bvc/?streamname=live_349pflag=1: End of file\n  [aac @ 0x5599e11787c0] Qavg: 801.218  Conversion failed!

FFMPEG_MP4_CODEC = '-threads 4 -vcodec libx264 -c:a aac -ac 2 -ar 44100 -ab 192k'
FFMPEG_RTMP_CODEC = '-threads 5 -vcodec libx264 -acodec aac -b:a 192k'
FFMPEG_AMIX_CODEC = '-threads 16 -vcodec copy  -acodec aac -b:a 192k'
FFMPEG_SUBTITLE = True
FFMPEG_FRAMERATE = 25
SUBTITLE_PATH = '/tmp/srt'

VIDEO_P = 'hd720'
VIDEO_FORMAT = 'flv'
IMG_SECONDS = 30
PLAYLIST_PATH = 'playlist.txt'

MP4_ROOT = '/tmp/mp4'
MP3_ROOT = 'aux'
IMG_FLODER = 'img'
SOURCE_ADUIO_FLODER = 'aux/coco'
CACHE_MP4_PATH = 'cache.mp4'

LOOP_LOOPLIST_PATH = 'looplist.txt'
LOOP_LOOP_MP4_PATH  = "/tmp/loop.mp4"
LOOP_NEXT_MP4_PATH  = "/tmp/next.mp4"           #next->loop
LOOP_TEMP_MP4_PATH  = "/tmp/temp.mp4"       #temp->next
LOOP_VOICE_M4A_PATH = "aux/voice"
LOOP_NO_AUDIO_MESSAGE_TIMES = 0
LOOP_AMIX_M4A_LIST = ['aux/voice/l1000.m4a','aux/voice/l1001.m4a','aux/voice/l1101.m4a','aux/voice/l1105.m4a','aux/voice/l1110.m4a','aux/voice/l2000.m4a','aux/voice/l2001.m4a']     #混音文件路径
LOOP_SECONDS_UPDATE = 15
LOOP_CAN_MAKE_NEXT= True      #锁，解锁需要在next->loop,loop开始播放后
LOOP_MAKE_TEMP_NEXT_LOOP = False        # no use
LOOP_DURATION_TOTAL = 0      #播放时长统计，用于解锁 LOOP_NEXT_HAS_MADE
LOOP_TIME_START = 9691647810
make_temp_next_loop_thread = None

# ffmpeg -i -loop 0 aux/coco/192k-CoCo-想你的365天.m4a -ss 0 -t 32695 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco102.jpg -filter_complex "[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv]" -map [outv] -map 0:a -r 25 -threads 10 -vcodec libx264 -acodec aac -b:a 192k -f  flv -listen 1  http://127.0.0.1:8080
FFMPEG_SAMPLE_RTMP_LIVE  = "ffmpeg -re -stream_loop -1 -i aux/coco/192k-CoCo-想你的365天.m4a -ss 0 -t 32695 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco101.jpg -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv]\" -map [outv] -map 0:a -r 25 -threads 10 -vcodec libx264 -acodec copy -hide_banner -copyts -f  flv {}"
#ffmpeg -re -stream_loop -1 -i list.txt -flush_packets 0 -f m
#FFMPEG_SAMPLE_RTMP_LIVE = "ffmpeg -re -stream_loop -1 -f concat -safe 0 -i looplist.txt  -r 25 -f flv -threads 5 -vcodec copy -acodec aac -b:a 192k {}"
# s=770x432 mp4=154M thread=0
# s=770x432 mp4=135M thread=2
# s=770x432 mp4=126M thread=1

# ffmpeg  -i aux/coco/李玟_想你的365天.mp3 -ss 0 -t 326.95 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco103.jpg -filter_complex "[1:v][2:v]overlay=x=0:y=0[outv];[0:0]concat=n=1:v=0:a=1[outa]" -map [outv] -map [outa] -vcodec libx264 -acodec aac -b:a 320k -f mp4 overlay_432p_a320k.mp4
# ffmpeg -i aux/coco/李玟-爱你爱到.m4a -ss 0 -t 261.328 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco132.jpg -filter_complex "[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv]" -map [outv] -map 0:a -r 25 -threads 2 -vcodec libx264 -acodec aac -y -f mp4 cache.mp4
#ffmpeg_mp4 = "ffmpeg -i {} -ss 0 -t {} -f lavfi -i color=c=0x000000:s=770x432:r=25 -i {} -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv];[0:0]concat=n=1:v=0:a=1[outa]\" -map [outv] -map [outa] -vcodec libx264 -acodec aac -y -f mp4 {}"
ffmpeg_mp4 = "ffmpeg -i {} -ss 0 -t {} -f lavfi -i color=c=0x000000:s=770x432:r={} -i {} -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0{}[outv]\" -map [outv] -map 0:a -r {} {} -hide_banner -copyts -y -f mp4 {}"
# ffmpeg -i aux/coco/192k-CoCo-想你的365天.m4a  -ss 0 -t 326.93 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco130.jpg  -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=0:0,subtitles=sample.srt:force_style='Fontsize=24'[outv]\" -map [outv] -map 0:a -r 25 -threads 10 -vcodec libx264   -acodec copy -f mp4 /tmp/mp4/sample_srt.mp4"
subtitle_para = ",subtitles={}:force_style='Fontsize=24'"
# ffmpeg -re -i sample_432p_a320k.mp4 -f flv -threads 2 -acodec aac -b:a 320k -vcodec copy rtmp
#ffmpeg_playlist = "ffmpeg -re -f concat -safe 0 -i playlist.txt -r 25  -f flv -threads 2 -vcodec libx264 -acodec aac {}"
ffmpeg_playlist = "ffmpeg -re -f concat -safe 0 -i {} -r  {}  -hide_banner -f flv {}  {}"
#FFMPEG_AMIX = "ffmpeg -i {} -i {} -filter_complex \"[1:a]adelay=delays={}|{}[aud1];[0:a][aud1]amix=inputs=2[outa]\" -map 0:v -map [outa] -r  {}  {} -hide_banner -copyts -y -f flv {}"
ffmpeg_looplist = "ffmpeg -re -stream_loop -1 -f concat -safe 0 -i looplist.txt  -r {} {} -hide_banner -f flv  {}"
# ffmpeg -re -stream_loop -1 -i szg_432p_171_192k.mp4 -r 25 -threads 2 -acodec aac -b:a 192k -vcodec copy -hide_banner -f flv  -listen 1 http://127.0.0.1:8080
ffmpeg_rtmp_mp4 = "ffmpeg -re -i {} -r {} {} -hide_banner -f flv  {}"
print('stream v5.7.1:mp4',ffmpeg_mp4)
print('stream v5.4.5:rtmp',ffmpeg_playlist)
print('stream v5.6.11:ffmpeg_looplist',ffmpeg_looplist)
print('stream v5.9.2:ffmpeg_rtmp_mp4',ffmpeg_rtmp_mp4)
Global_Amix_Queue = Queue()  # 创建一个队列对象
##############################################
# # 以第一个视频分辨率作为全局分辨率
# # 视频分辨率相同可以使用copy?{"cmd":"ffmpeg -re -f concat -safe 0 -i playlist.txt -f flv -codec copy -listen 1  http://127.0.0.1:8080"}
# # ffmpeg -re -f concat -safe 0 -i playlist.txt -f flv -threads 2 -acodec aac -b:a 320k -vcodec libx264 -listen 1 http://127.0.0.1:8080
# # ffmpeg -re -f concat -safe 0 -i playlist.txt -f flv -threads 2 -acodec aac -b:a 320k -vcodec copy -listen 1 http://127.0.0.1:8080
# # ffmpeg -re -f concat -safe 0 -i playlist.txt -f flv -acodec aac -vcodec libx264 rtmp
# # ffplay -f flv http://127.0.0.1:8080
##############################################
# playlist.txt
# file 'sample_720p_a320k.mp4'
# file 'sample_480p_a320k.mp4'
# #file 'sample_432p_a320k.mp4'
##############################################
# ffmpeg -i sample_432p_a320k.mp4 -vf subtitles=subtitle.cn.srt output_srt.mp4
# ffmpeg -re -i sample_432p_a320k.mp4  -f flv -threads 6 -vcodec libx264 -acodec copy -vf subtitles=subtitle.flc -listen 1 http://127.0.0.1:8080
# FFMPEG::return: 137 您的实例 [web1] 使用内存量超出该实例规格，导致进程 OOM 退出。但是下载的还在
########################## rtmp ###############################
def ffmpeg_status():
    looplist = False
    playlist = False
    playmp4 = False
    process_info = shell.process_info("ffmpeg")
    if process_info:
        cmdline = process_info.get('cmdline')
        if PLAYLIST_PATH in cmdline:
            playlist = True
        if LOOP_LOOPLIST_PATH in cmdline:
            looplist = True
        if LOOP_LOOP_MP4_PATH in cmdline:
            playmp4 = True
        if looplist or playlist or playmp4:
            return {
                "pid":process_info.get('pid'),
                "name":process_info.get('name'),
                "status":process_info.get('status'),
                "cpu_percent":process_info.get('cpu_percent'),
                "memory_info":process_info.get('memory_info'),
                "playlist":playlist,
                "looplist":looplist,
                "playmp4":playmp4
            }
        else:
            return {
                "pid":process_info.get('pid'),
                "name":process_info.get('name'),
                "status":process_info.get('status'),
                "cpu_percent":process_info.get('cpu_percent'),
                "memory_info":process_info.get('memory_info'),
                "playlist":False,
                "looplist":False,
                "playmp4":False
            }
    return None
def test_(str_rtmp,total,codec=FFMPEG_MP4_CODEC,framerate=FFMPEG_FRAMERATE,max_memory=MAX_MEMORY,subtitle=FFMPEG_SUBTITLE,floder_list=['']):
    str_rtmp = '\"{}\"'.format(str_rtmp)
    return FFMPEG_SAMPLE_RTMP_LIVE.format(str_rtmp)

def rtmp_mp4(str_rtmp,codec=FFMPEG_RTMP_CODEC,framerate=FFMPEG_FRAMERATE):
    """
    返回rtmp rtmp_mp4 的cmd，need启动替换loop.mp4的线程，适时根据loop.mp4的时长，用新的temp.mp4替换loop.mp4
    替换cache.mp4的线程需要马上开始混音，并生成temp.mp4，保证在loop播完前生成
    :param str_rtmp:'"rtmp://"'
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_RTMP_CODEC
    :return: ffmpeg cmd
    """
    global LOOP_DURATION_TOTAL
    global LOOP_TIME_START
    print('try rtmp_mp4 LOOP_DURATION_TOTAL:{}  LOOP_TIME_START:{}'.format(LOOP_DURATION_TOTAL,LOOP_TIME_START))
    if not framerate:
        framerate = FFMPEG_FRAMERATE
    str_rtmp = '\"{}\"'.format(str_rtmp)
    mp4list = mp3list(MP4_ROOT)
    if len(mp4list) == 0:
        help_loop()
    cmd = ffmpeg_rtmp_mp4.format(LOOP_LOOP_MP4_PATH,framerate,codec,str_rtmp)
    #LOOP_TIME_START = int(time.time()) #need change in cloud
    return cmd

def reset_time_start():
    """
    :return: LOOP_TIME_START
    """
    global LOOP_TIME_START
    LOOP_TIME_START = int(time.time()) #need change in cloud
    return LOOP_TIME_START

def make_temp_next(adelay=10000,codec=FFMPEG_AMIX_CODEC,framerate=FFMPEG_FRAMERATE):
#def amix_next(mp4,mix_m4a_list,adelay=10000,codec=FFMPEG_AMIX_CODEC,framerate=FFMPEG_FRAMERATE):
    """
    混音，生成temp.mp4，保证在loop.mp4播完前60s生成
    :param name:=预先生成的mp4 path
    :param mix_m4a_list:=混入语音path，no no no 如果空，不混音，直接延时复制
    :param adelay:=混入语音adelay ms
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_MP4_CODEC
    :return: T/F
    """
    global LOOP_CAN_MAKE_NEXT
    global LOOP_DURATION_TOTAL
    global LOOP_NO_AUDIO_MESSAGE_TIMES
    LOOP_CAN_MAKE_NEXT = False

    ret = 9
    now = int(time.time())
    before_timeout = 90 #歌曲结束前90必须处理
    probe = ffmpeg.probe(LOOP_LOOP_MP4_PATH)
    format = probe.get('format')
    last_loop_duration = int(float(format.get('duration')) )     #seconds
    print('next_mp4:TIME_START={},DURATION_LAST={},t={}'.format(LOOP_TIME_START,last_loop_duration,now-LOOP_TIME_START))
    if LOOP_TIME_START +  last_loop_duration -before_timeout < now:
        voice_obj = class_voice.get_amix_voice()
        # 语音文件是一定有的
        amix = voice_obj.get('amix')
        print(voice_obj)
        amix = process_amix(amix,3)
        print('process_amix:',amix)
        if voice_obj.get('hasmsg'):
            LOOP_NO_AUDIO_MESSAGE_TIMES = 0
        else:
            print('No mix audio message,LOOP_NO_AUDIO_MESSAGE_TIMES={}'.format(LOOP_NO_AUDIO_MESSAGE_TIMES))
            if 0 < LOOP_NO_AUDIO_MESSAGE_TIMES:
                return 2
            LOOP_NO_AUDIO_MESSAGE_TIMES += 1
        mp4 = voice_obj.get('mp4')
        if mp4:
            mp4 = os.path.join(MP4_ROOT, mp4)
        else:
            mp4list = mp3list(MP4_ROOT)
            mp4 = mp4list[0]
        if amix_next_mp4(mp4,amix,adelay=adelay,framerate=framerate):
            try:
                os.rename(LOOP_TEMP_MP4_PATH,LOOP_NEXT_MP4_PATH)
                return 0
            except:
                print('Error probe:',mp4,amix)
        else:
            # #失败，补救
            shutil.copy(mp4,LOOP_NEXT_MP4_PATH)
        # FFMPEG_AMIX = "ffmpeg -i {} -i {} -filter_complex \"[1:a]adelay=delays={}|{}[aud1];[0:a][aud1]amix=inputs=2[outa]\" -map 0:v -map [outa] -r  {}  {} -copyts -y -f flv {}"
        # cmd = FFMPEG_AMIX.format(mp4,amix[0].get('path'),adelay,adelay,framerate,codec,LOOP_TEMP_MP4_PATH)
        # #ret = shell.OutputShell(cmd,False)
        # ret = shell.ShellRun(cmd,False,False,False)
        # if 0==ret:
        #     try:
        #         os.rename(LOOP_TEMP_MP4_PATH,LOOP_NEXT_MP4_PATH)
        #         return ret
        #     except:
        #         print('Error probe:',LOOP_TEMP_MP4_PATH)
        # #失败，补救
        # print('Error shell cmd:',cmd)
        # shutil.copy(mp4,LOOP_NEXT_MP4_PATH)
    return ret

def amix_next_mp4(mp4,amix,adelay=10000,framerate=25):
    t_start = time.time()
    ret = False
    main = ffmpeg.input(mp4)
    main_v = main.video
    main_a = main.audio
    a_in_arr = []
    for a_obj in amix:
        ina = ffmpeg.input(a_obj.get('path'))
        a_in_arr.append(ina)
    joined = ffmpeg.concat(*a_in_arr, v=0,a=1).node
    a_contac = joined[0]
    a_delay = ffmpeg.filter(a_contac,filter_name='adelay',delays='{}|{}'.format(adelay,adelay))
    a_mix = ffmpeg.filter([main_a,a_delay],filter_name='amix',inputs='2')
    try:
        out, err = (ffmpeg
            .output(
                main_v,
                a_mix,
                LOOP_TEMP_MP4_PATH,
                loglevel='quiet',
                threads='8',
                r=str(framerate),
                vcodec='copy',
                acodec='aac',
                ac='2',
                ar='44100',
                ab='192k',
                f='flv')
            .overwrite_output()
            .run(cmd=["ffmpeg"])#capture_stderr=True)
        )
        ret = True
    except ffmpeg.Error as error:
        print('Error ffmpeg:',mp4,amix)
        ret = False
    print('amix_next_mp4:seconds=',time.time()-t_start)
    return ret

def process_amix(amix,times=3):
    """
    多次记录礼物语音，后面再取出使用，返回本次的语音包
    :param amix:amix
    :param times:echo times
    :return: amix
    """
    global Global_Amix_Queue
    ret = []
    if not Global_Amix_Queue.empty():
        a_gift = Global_Amix_Queue.get()
        ret.append(a_gift)
    gift_num = len(ret)
    for a in amix:
       if 0 < gift_num:
           if a.get('type')==ret[0].get('type'):
               # 礼物回声时，避免重复的语音
               pass
       ret.append(a)
    for i in range(times):
        for a in amix:
            if a.get('type')>=30000:
                # gift voice, record in queue
                Global_Amix_Queue.put(a)
    return ret
######################################################
def rtmp_loop(str_rtmp,codec=FFMPEG_RTMP_CODEC,framerate=FFMPEG_FRAMERATE):
    """
    返回rtmp looplist 的cmd，并启动替换loop.mp4的线程，适时根据loop.mp4的时长，用新的temp.mp4替换loop.mp4
    替换cache.mp4的线程需要马上开始混音，并生成temp.mp4，保证在loop播完前生成
    :param str_rtmp:'"rtmp://"'
    :param total:=MP4_TOTAL_PLAY:最多串接文件个数
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_RTMP_CODEC
    :return: ffmpeg cmd
    """
    global LOOP_DURATION_TOTAL
    global LOOP_TIME_START
    global make_temp_next_loop_thread
    print('try rtmp_loop LOOP_DURATION_TOTAL:{}  LOOP_TIME_START:{}'.format(LOOP_DURATION_TOTAL,LOOP_TIME_START))
    if not framerate:
        framerate = FFMPEG_FRAMERATE
    str_rtmp = '\"{}\"'.format(str_rtmp)
    mp4list = mp3list(MP4_ROOT)
    if len(mp4list) == 0:
        help_loop()
    cmd = ffmpeg_looplist.format(framerate,codec,str_rtmp)
    LOOP_DURATION_TOTAL = 0      #播放时长统计，用于解锁 LOOP_NEXT_HAS_MADE
    LOOP_TIME_START = int(time.time())
    return cmd

def make_temp_next_loop(adelay=10000,codec=FFMPEG_AMIX_CODEC,framerate=FFMPEG_FRAMERATE):
#def amix_next(mp4,mix_m4a_list,adelay=10000,codec=FFMPEG_AMIX_CODEC,framerate=FFMPEG_FRAMERATE):
    """
    混音，生成temp.mp4，保证在loop.mp4播完前60s生成
    :param name:=预先生成的mp4 path
    :param mix_m4a_list:=混入语音path，no no no 如果空，不混音，直接延时复制
    :param adelay:=混入语音adelay ms
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_MP4_CODEC
    :return: T/F
    """
    global LOOP_CAN_MAKE_NEXT
    global LOOP_DURATION_TOTAL
    LOOP_CAN_MAKE_NEXT = False

    ret = 9
    now = int(time.time())
    before_timeout = 90 #歌曲结束前90必须处理
    print('make_temp_next_loop:TIME_START={},DURATION_TOTAL={},t={}'.format(LOOP_TIME_START,LOOP_DURATION_TOTAL,now-LOOP_TIME_START))
    probe = ffmpeg.probe(LOOP_LOOP_MP4_PATH)
    format = probe.get('format')
    last_loop_duration = float(format.get('duration'))      #seconds
    if LOOP_TIME_START + LOOP_DURATION_TOTAL + last_loop_duration -before_timeout < now:
        while LOOP_TIME_START + LOOP_DURATION_TOTAL< now:
            # 万一now太超前，跳过应该next的歌，直接切到now对应的歌
            LOOP_DURATION_TOTAL += last_loop_duration
        voice_arr = class_voice.get_amix_voice()
        if voice_arr:
            mix_list = []
            for file_name in voice_arr:
                file_path = os.path.join(LOOP_VOICE_M4A_PATH, file_name)
                if  os.path.exists(file_path):
                    mix_list.append(file_path)
            if(len(mix_list)==0):
                print('No mix audio file:',LOOP_TEMP_MP4_PATH)
                return help_loop()
        else:
            print('No mix audio message:not change loop',LOOP_TEMP_MP4_PATH)
            return 0# help_loop()
        mp4list = mp3list(MP4_ROOT)
        mp4 = mp4list[0]
        FFMPEG_AMIX = "ffmpeg -i {} -i {} -filter_complex \"[1:a]adelay=delays={}|{}[aud1];[0:a][aud1]amix=inputs=2[outa]\" -map 0:v -map [outa] -r  {}  {} -copyts -y -f flv {}"
        cmd = FFMPEG_AMIX.format(mp4,mix_list[random.randint(0,len(mix_list)-1)],adelay,adelay,framerate,codec,LOOP_TEMP_MP4_PATH)
        #ret = shell.OutputShell(cmd,False)
        ret = shell.ShellRun(cmd,False,False,False)
        if 0==ret:
            try:
                os.rename(LOOP_TEMP_MP4_PATH,LOOP_NEXT_MP4_PATH)
                rename_next_loop(LOOP_NEXT_MP4_PATH,LOOP_LOOP_MP4_PATH)
                return ret
            except:
                print('Error probe:',LOOP_TEMP_MP4_PATH)
        #失败，补救
        print('Error shell cmd:',LOOP_TEMP_MP4_PATH)
        shutil.copy(mp4,LOOP_NEXT_MP4_PATH)
        rename_next_loop(LOOP_NEXT_MP4_PATH,LOOP_LOOP_MP4_PATH)
    return ret

def rename_next_loop(next=LOOP_NEXT_MP4_PATH,loop=LOOP_LOOP_MP4_PATH):
    if print_video_info(next) and  print_video_info(loop):
        os.rename(next,loop)
    # cmd = 'mv -f {} {}'.format(next,loop)
    # shell.OutputShell(cmd)

def print_video_info(file_path):
    if os.path.exists(file_path):
        probe = ffmpeg.probe(file_path)
        format = probe.get('format')
        tags = format.get('tags')
        print('{} title:{} artist:{} duration:{} '.format(file_path,tags.get('title'),tags.get('artist'),format.get('duration')))
        return True
    else:
        print(':::::NO FILE:::::{} not exists'.format(file_path))
        return False

def help_loop():
    """
    救命
    """
    mp4list = mp3list(MP4_ROOT)
    if len(mp4list) == 0:
        shutil.copy(BAK_MP4_PATH,LOOP_LOOP_MP4_PATH)
    else:
        shutil.copy(mp4list[0],LOOP_NEXT_MP4_PATH)
        rename_next_loop(LOOP_NEXT_MP4_PATH,LOOP_LOOP_MP4_PATH)
    return True

def rtmp_loop_reset():
    global LOOP_MAKE_TEMP_NEXT_LOOP
    LOOP_MAKE_TEMP_NEXT_LOOP = False

######################################################

def rtmp_concat_mp4(str_rtmp,total,codec=FFMPEG_RTMP_CODEC,framerate=FFMPEG_FRAMERATE,max_memory=MAX_MEMORY,floder_list=['']):
    """
    获取floder_list下所有path mp3的串接cmd，不够total的话，复制自身补足
    :param str_rtmp:'"rtmp://"'
    :param total:=MP4_TOTAL_PLAY:最多串接文件个数
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_RTMP_CODEC
    :return: ffmpeg cmd
    """
    if not framerate:
        framerate = FFMPEG_FRAMERATE
    procs = shell.procs_info("ffmpeg")
    if procs:
        shell.OutputShell('ls {} -l'.format(MP4_ROOT),True)
        print('ffmpeg in procs,pass')
        return
    str_rtmp = '\"{}\"'.format(str_rtmp)
    root_list = mp3list(MP4_ROOT)
    mp4list=[]
    mp4_total = len(root_list)
    if mp4_total > 0:
        # 不够total的话，复制自身补足
        total_size = 0
        CONST_MB = float(1024 * 1024)
        for lo in range(0,int(total/mp4_total)+1):
            if len(mp4list) >=total:
                    break
            for file_path in root_list: 
                if len(mp4list) >= total:
                    break
                mp4list.append(file_path)
        mem_list = []
        for file_path in mp4list: 
            fsize = os.path.getsize(file_path) / CONST_MB
            if total_size + fsize > max_memory:
                break
            mem_list.append(file_path)
            total_size += fsize
        total_seconds = write_playlist(mem_list)
        print('total seconds:{} hours:{} total size:{}'.format(total_seconds,total_seconds/60/60,total_size))
        cmd = ffmpeg_playlist.format(PLAYLIST_PATH,framerate,codec,str_rtmp)
    else:
        # return 实时生成 flv
        cmd = FFMPEG_SAMPLE_RTMP_LIVE.format(str_rtmp)
    #print(cmd)
    return cmd#shell.OutputShell(cmd,True)

def write_playlist(mp3_list):
    """
    根据mp3_list,write playlist.txt
    :param mp3_list:['fullpath']
    :return: duration_total
    """
    duration_total = 0
    file_total = 0
    lineArray = []
    now = int(datetime.timestamp(datetime.now()))
    
    for file_path in mp3_list:
        audio_info = get_audio_info(file_path)
        if audio_info:
            duration = audio_info.get('duration')
            date_time = datetime.fromtimestamp(now+int(duration_total))
            lineArray.append("# {}".format(date_time))
            lineArray.append("file \'{}\'".format(file_path))
            duration_total += duration
            file_total += 1
        else:
            print('error ffprobe:',file_path)
    date_time = datetime.fromtimestamp(now+int(duration_total))
    lineArray.append("# Total:{}: {}".format(file_total,date_time))
    lineArray.append("# rem")
    playlist_str = '\r\n'.join(lineArray)
    playlist = open(PLAYLIST_PATH, 'w')
    playlist.write(playlist_str)
    playlist.close()
    print(playlist_str)
    return duration_total

########################## mp4 ###############################
def map_video_audio_mp4(total,codec=FFMPEG_MP4_CODEC,framerate=FFMPEG_FRAMERATE,subtitle=FFMPEG_SUBTITLE):
    """
    获取SOURCE_ADUIO_FLODER下m4a，转mp4
    :param total:=MP3_TOTAL_PLAY:最多个数
    :param framerate:=FFMPEG_FRAMERATE
    :param codec:=FFMPEG_MP4_CODEC
    :return: ls MP4
    """
    if not framerate:
        framerate = FFMPEG_FRAMERATE
    procs = shell.procs_info("ffmpeg")
    if procs:
        shell.OutputShell('ls {} -l'.format(MP4_ROOT),True)
        print('ffmpeg in procs,pass')
        return
    m4alist = mp3list(SOURCE_ADUIO_FLODER)
    imglist = mp3list(IMG_FLODER)
    print("map_video_audio_mp4():",total)
    # 先做mp4list里面没有的
    done_num = 0
    for m4a in m4alist:
        if done_num >= total:
                break
        name = file_name(m4a)
        mp4_path = '{}/{}.mp4'.format(MP4_ROOT,name)
        # 更新mp4list
        mp4list = mp4list_by_time(MP4_ROOT)
        print('mp4:',done_num,MP4_ROOT,len(mp4list))
        img = imglist[done_num % len(imglist)]     #imglist must too large
        if not mp4_path in mp4list:
            #没有
            ret = ai_to_mp4(m4a,img,codec=codec,framerate=framerate,subtitle=FFMPEG_SUBTITLE)
            if 0 == ret:
                print('ok',done_num,m4a,img)
            else:
                shell.OutputShell('ls {} -l'.format(MP4_ROOT),True)
                print('ffmpeg not return 0',done_num,m4a,img)
                return
            done_num += 1
            time.sleep(3)
    print('mp4list里面没有的,OK')
    # mp4list里面没有的，做完，这里就是都有的了,先最老,mp4list[0]
    # 对MP4_ROOT/sample_432p_a320k.mp4 pass
    mp4_m4a_list = []
    mp4list = mp4list_by_time(MP4_ROOT)
    print('mp4:',done_num,MP4_ROOT,len(mp4list))
    for mp4 in mp4list:
        name = file_name(mp4)
        mp4_src_m4a_path = '{}/{}.m4a'.format(SOURCE_ADUIO_FLODER,name)
        if mp4_src_m4a_path in m4alist:
            mp4_m4a_list.append({"mp4":mp4,"m4a":mp4_src_m4a_path})
    for mp4_m4a in mp4_m4a_list:
        if done_num >= total:
            break
        m4a = mp4_m4a['m4a']
        img = imglist[done_num % len(imglist)]     #imglist must too large
        ret = ai_to_mp4(m4a,img,codec=codec,framerate=framerate,subtitle=FFMPEG_SUBTITLE)
        if 0 == ret:
            print('ok',done_num,m4a,img)
        else:
            shell.OutputShell('ls {} -l'.format(MP4_ROOT),True)
            print('ffmpeg not return 0',done_num,m4a,img)
            return
        done_num += 1
        time.sleep(3)
    print('mp4list里面有的,OK')
    shell.OutputShell('ls {} -l'.format(MP4_ROOT),True)
    return done_num

def ai_to_mp4(m4a,img,codec=FFMPEG_MP4_CODEC,framerate=FFMPEG_FRAMERATE,subtitle=FFMPEG_SUBTITLE):
    name = file_name(m4a)
    if subtitle:
        class_subtitle.update_subtitle_file(name)
    probe = ffmpeg.probe(m4a)
    format = probe.get('format')
    t = int(float(format.get('duration'))+1)
    #streams = probe.get('streams')
    #print(m4a,streams)
    sub_para = ''
    if subtitle:
        subtitle_path = os.path.join(SUBTITLE_PATH, name+'.srt')
        if os.path.exists(subtitle_path):
            sub_para = subtitle_para.format(subtitle_path)
        else:
            print('No subtitle of this audio:',m4a)
    cmd = ffmpeg_mp4.format(m4a,t,framerate,img,sub_para,framerate,codec,CACHE_MP4_PATH)
    #ret = shell.OutputShell(cmd,False)
    ret = shell.ShellRun(cmd,False,False,False)
    if 0 == ret:
        mp4_path = os.path.join(MP4_ROOT, name+'.mp4')   #'{}/{}.mp4'.format(MP4_ROOT,name)
        shutil.copy(CACHE_MP4_PATH,mp4_path)
        #os.rename(CACHE_MP4_PATH,mp4_path)
    return ret

def file_name(fullpath,ext=3):
    # 无扩展名
    names = fullpath.split('/')
    name = names[len(names)-1]
    return name[0:-ext-1]

def mp4list_by_time(path=SOURCE_ADUIO_FLODER):
    """
    获取mp4最近修改（modify）时间,path列表
    :param path:
    :return:
    """
    # os.path.getctime()：获取文件创建（create）时间
    # os.path.getatime()：获取文件最近访问（access）时间
    # os.path.getmtime()：获取文件最近修改（modify）时间
    mp3list = []
    file_list = []
    if os.path.exists(path):
        for file_name in os.listdir(path):
            #print(os.path.join(path, file_name))
            file_list.append(os.path.join(path, file_name))
        # 获取按照文件时间修改排序的列表，默认是按时间升序
        mp3list = sorted(file_list, key=lambda file: os.path.getmtime(file))
        #random.shuffle(mp3list)
    return mp3list

########################## base ###############################
def get_audio_info(file_path):
    """
    获取mp3/aac音频文件时长
    :param file_path:
    :return:
    """
    title = None
    artist = None
    duration = 0
    try:
        probe = ffmpeg.probe(file_path)
        format = probe.get('format')
        duration = float(format.get('duration'))
        if format.get('tags'):
            tags = format.get('tags')
            if tags.get('title'):
                title = tags.get('title')
            if tags.get('artist'):
                artist = tags.get('artist')
    except:
        return None
    return {'duration':duration,'title':title,'artist':artist}

def mp3list(path="a/coco"):
    """
    获取mp3音频文件path列表
    :param path:
    :return:
    """
    mp3list = []
    if os.path.exists(path):
        for file_name in os.listdir(path):
            mp3list.append(path+'/' +file_name)
        random.shuffle(mp3list)
    return mp3list

if __name__ == '__main__':
    # python stream.py m/r num
    # <class 'list'> ['test.py', 'm', '5']
    rtmp= "http://127.0.0.1:8080"
    argv = sys.argv
    print(type(argv),argv)
    try:
        argv = sys.argv[1]
        if 'r'==argv:
            rtmp_concat_mp4('rtmp',int(sys.argv[2]))
        if 'm'==argv:
            map_video_audio_mp4(int(sys.argv[2]))
        else:
            name = '192k-CoCo-想你的365天'
            print('map sample mp4:',name)
            ai_to_mp4(os.path.join(SOURCE_ADUIO_FLODER, name+'.m4a'),'img/art_coco135.jpg')
    except:
        print('No argv or error, sample: python stream.py m/r num')
        print("{\"cmd\":\"python stream.py m  5\"}","mp4")
        print("{\"cmd\":\"python stream.py r  5\"}","rtmp")
