# coding: utf-8
import ffmpeg
import os
import sys
import random
import time
import shutil 
import shell as shell

FFMPEG_MP4_CODEC = '-threads 2 -vcodec libx264 -acodec aac -b:a 192k'
FFMPEG_RTMP_CODEC = '-threads 2 -vcodec libx264 -acodec aac -b:a 192k'

FFMPEG_FRAMERATE = 25
VIDEO_P = 'hd720'
VIDEO_FORMAT = 'flv'
IMG_SECONDS = 30
PLAYLIST_PATH = 'playlist.txt'

MP4_ROOT = '/tmp/mp4'
MP3_ROOT = 'aux'
IMG_FLODER = 'img'
SOURCE_ADUIO_FLODER = 'aux/coco'
CACHE_MP4_PATH = 'cache.mp4'

# s=770x432 mp4=154M thread=0
# s=770x432 mp4=135M thread=2
# s=770x432 mp4=126M thread=1

# ffmpeg  -i aux/coco/李玟_想你的365天.mp3 -ss 0 -t 326.95 -f lavfi -i color=c=0x000000:s=770x433:r=25 -i img/art_coco103.jpg -filter_complex "[1:v][2:v]overlay=x=0:y=0[outv];[0:0]concat=n=1:v=0:a=1[outa]" -map [outv] -map [outa] -vcodec libx264 -acodec aac -b:a 320k -f mp4 overlay_432p_a320k.mp4
# ffmpeg -i aux/coco/李玟-爱你爱到.m4a -ss 0 -t 261.328 -f lavfi -i color=c=0x000000:s=770x432:r=25 -i img/art_coco132.jpg -filter_complex "[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv]" -map [outv] -map 0:a -r 25 -threads 2 -vcodec libx264 -acodec aac -y -f mp4 cache.mp4
#ffmpeg_mp4 = "ffmpeg -i {} -ss 0 -t {} -f lavfi -i color=c=0x000000:s=770x432:r=25 -i {} -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv];[0:0]concat=n=1:v=0:a=1[outa]\" -map [outv] -map [outa] -vcodec libx264 -acodec aac -y -f mp4 {}"
ffmpeg_mp4 = "ffmpeg -i {} -ss 0 -t {} -f lavfi -i color=c=0x000000:s=770x432:r={} -i {} -filter_complex \"[2:v]scale=770:432[v2];[1:v][v2]overlay=x=0:y=0[outv]\" -map [outv] -map 0:a -r {} {} -y -f mp4 {}"
# ffmpeg -re -i sample_432p_a320k.mp4 -f flv -threads 2 -acodec aac -b:a 320k -vcodec copy rtmp
#ffmpeg_playlist = "ffmpeg -re -f concat -safe 0 -i playlist.txt -r 25  -f flv -threads 2 -vcodec libx264 -acodec aac {}"
ffmpeg_playlist = "ffmpeg -re -f concat -safe 0 -i playlist.txt -r  {}  -f flv {}  {}"
print('stream v5.0.3:mp4',ffmpeg_mp4)
print('stream v5.0.1:rtmp',ffmpeg_playlist)
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
# FFMPEG::return: 137 您的实例 [web1] 使用内存量超出该实例规格，导致进程 OOM 退出。但是下载的还在
########################## rtmp ###############################
def rtmp_concat_mp4(str_rtmp,total,codec=FFMPEG_RTMP_CODEC,framerate=FFMPEG_FRAMERATE,floder_list=['']):
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
    for file_path in root_list: 
        mp4list.append(file_path)
        if len(mp4list) >= total:
            break
    total_seconds = write_playlist(mp4list)
    print('total seconds:',total_seconds)
    cmd = ffmpeg_playlist.format(framerate,codec,str_rtmp)
    #print(cmd)
    return cmd#shell.OutputShell(cmd,True)

def write_playlist(mp3_list):
    """
    根据mp3_list,write playlist.txt
    :param mp3_list:['fullpath']
    :return: duration_total
    """
    duration_total = 0
    lineArray = []
    
    for file_path in mp3_list:
        lineArray.append("file \'{}\'".format(file_path))
        audio_info = get_audio_info(file_path)
        duration = audio_info.get('duration')
        duration_total += duration
    lineArray.append("# rem")
    playlist_str = '\r\n'.join(lineArray)
    playlist = open(PLAYLIST_PATH, 'w')
    playlist.write(playlist_str)
    playlist.close()
    print(playlist_str)
    return duration_total

########################## mp4 ###############################
def map_video_audio_mp4(total,codec=FFMPEG_MP4_CODEC,framerate=FFMPEG_FRAMERATE):
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
            ret = ai_to_mp4(m4a,img,codec=codec,framerate=framerate)
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
        ret = ai_to_mp4(m4a,img,codec=codec,framerate=framerate)
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

def ai_to_mp4(m4a,img,codec=FFMPEG_MP4_CODEC,framerate=FFMPEG_FRAMERATE):
    name = file_name(m4a)
    probe = ffmpeg.probe(m4a)
    format = probe.get('format')
    t = float(format.get('duration'))
    cmd = ffmpeg_mp4.format(m4a,t,framerate,img,framerate,codec,CACHE_MP4_PATH)
    print(cmd)
    ret = shell.OutputShell(cmd,False)
    if 0 == ret:
        mp4_path = '{}/{}.mp4'.format(MP4_ROOT,name)
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
    probe = ffmpeg.probe(file_path)
    format = probe.get('format')
    duration = float(format.get('duration'))
    if format.get('tags'):
        tags = format.get('tags')
        if tags.get('title'):
            title = tags.get('title')
        if tags.get('artist'):
            artist = tags.get('artist')
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
    except:
        print('No argv or error, sample: python stream.py m/r num')
        print("{\"cmd\":\"python stream.py m  5\"}","mp4")
        print("{\"cmd\":\"python stream.py r  5\"}","rtmp")