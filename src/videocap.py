# -*- coding: UTF-8 -*-
import json
import os
import shutil
import sys
import threading
import time

import cv2

import gParam
from utils.utils import setting


class VCAP(threading.Thread):
    """
        截图保存到磁盘目录
    """
    video = None

    def __init__(self, video=None):
        """videocap的逻辑
            默认video_path 是存放视频的路径，此时截取录像内容
            video_path==False: 截取setting中addr的视频流
            viedo_path!=False 且 video!=None: 截取本地视频
            其他情况下 报错 并主动修改setting关闭各项功能
        args:
            video: 视频地址, 当不输入视频地址的时候默认None
        """
        threading.Thread.__init__(self)
        self.video = video
        self.video_path = gParam.Video_Path
        self.setting_path = gParam.Setting_Json
        self.videosplit_path = gParam.VideoSplit_Path
        # 这个判断主要是不确定当有多个摄像头都要求截图的时候怎么办，要求分析已保存的视频的时候怎么办
        # if video:
        #     print("我还没想好")
        #     self.video_path = gParam.Video_Path
        
    
    def capvideo(self):
        while True:
            status = {}
            with open(self.setting_path) as f:
                status = json.load(f)
            if status['status'] == 'run':
                try:
                    if self.video_path and self.video!= None:
                        print('videocap-----video_path', self.video_path)
                        path=os.path.join(self.video_path,self.video)
                        cap = cv2.VideoCapture(path)
                    elif self.video_path and self.video==None:
                        print("videocap-----系统已自动关闭图像抓取，请指定url或视频名后再打开")
                        setting(status='stop', writing=True)
                        continue
                    else:
                        print("尝试连接摄像头", status['addr'])
                        cap = cv2.VideoCapture(status['addr'])
                        print('videocap-----连接摄像头成功')
                except:
                    print('videocap-----连接摄像头失败')
                    setting(status='stop', writing=True)
                    continue
                
                count_num = 0
                print('---------------------------------------')
                while cap.isOpened():
                    count_num += 1
                    cur_time = str(time.time())
                    name = cur_time + '.jpg'
                    
                    ret, frame = cap.read()
                    if(count_num % 18 == 0):
                        try:
                            path=os.path.join(self.videosplit_path,name)
                            cv2.imwrite(path, frame)
                            # print('抓取图像', name)
                            time.sleep(0.5)
                        except:
                            print("videocap-----存储抓取的图像时出错")
                    
                    if ret == False:
                        setting(status='stop', command='none', writing=True)
                    data = {}
                    with open(self.setting_path) as f:
                        data = json.load(f)
                    if data['status'] == 'stop':
                        cap.release()
                        print('--------------------------------------')
                        print('videocap-----停止抓取图像')
                        break
            else:
                print("videocap-----心跳响应")
                time.sleep(2)


            

    def run(self):
        self.capvideo()


if __name__ == '__main__':
    # file=sys.argv[1]           #文件名
    file="1.mp4"           #文件名

    t3 = VCAP(file)

    t3.start()
