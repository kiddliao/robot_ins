# -*- coding: UTF-8 -*-
import base64
import io
import json
import os
import string
import threading
import time
from socket import *

import numpy as np
import redis
from pymongo import *

import gParam
from facedetect import FaceDetect
from inspection import Inspection
from mongo.mongodb import features_write, person_write
from newthread import NewThread
from periodins import MultiObjects_yolov3
from smokingins import Smoking_yolo3
from utils.utils import setting
from videocap import VCAP


class Event(threading.Thread):
    """事件响应类，要想开启事件响应功能，只需要创建并开启实例，指定属性（TaskID），修改event_setting.json，建立对应的报文发送线程即可
    args:
        e_face: bool, 是否开启人脸检测功能
        e_helmet: bool, 是否开启安全帽检测功能
        e_smoking: bool, 是否开启吸烟检测功能
    attr:
        self.period: int, 事件响应检测周期
        self.TaskID: string, 设定存入redis缓存的key
    """
    def __init__(self, e_face=False, e_helmet=False, e_smoking=False, TaskID='4396'):
        threading.Thread.__init__(self)
        self.e_face = e_face
        self.e_helmet = e_helmet
        self.e_smoking = e_smoking
        if e_face:
            self.e_face = FaceDetect()
        if e_helmet:
            self.e_helmet = MultiObjects_yolov3('yolo')
        if e_smoking:
            self.e_smoking = Smoking_yolo3('tiny')
        
        self.period = 10
        self.TaskID = '4396'
        self.rq = redis.Redis(host='127.0.0.1', port=6379)
    
    def helmet_event(self):
        """检测未戴安全帽事件
        当图片中出现head的时候，则触发报文发送,我们负责将要发送的内容放入缓存
        报文格式为:{
            'Command': 'Event',
            'TaskID': str,
            'EventNumber': int, 1
            'SubEvent': str, 'OffHelmet'
            'Eventtime': str, 时间戳形式
            'EventPic': str, 图片的base64编码 
        }
        """
        sw_ret = self.e_helmet.event_detect_video()
        if 'head' in sw_ret.keys():
            eventpic = ''
            with open(sw_ret['file'], 'rb') as f:
                eventpic = base64.b64encode(f.read())
                eventpic = str(eventpic)
            # eventtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            eventtime = time.time()
            data_dict = {
                'Command': 'Event',
                'TaskID': self.TaskID,
                'EventNumber': 1,
                'SubEvent': 'OffHelmet',
                'Eventtime': eventtime,
                'EventPic': eventpic
            }
            data_dict['contentLength'] = len(str(data_dict))+13+10
            json_data = json.dumps(data_dict)
            self.rq.lpush(self.TaskID, json_data)
            print("安全帽事件", sw_ret)
        elif sw_ret=={}:
            print("应该是出现了错误，没有找到图片")
        else:
            print("没有没带安全帽的现象")

    def smoking_event(self):
        """检测吸烟事件
        """
        sw_ret = self.e_smoking.event_smoking()
        if 'cigarette' in sw_ret.keys():
            eventpic = ''
            with open(sw_ret['file'], 'rb') as f:
                eventpic = base64.b64encode(f.read())
                eventpic = str(eventpic)
            # eventtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            eventtime = time.time()
            data_dict = {
                'Command': 'Event',
                'TaskID': self.TaskID,
                'EventNumber': 1,
                'SubEvent': 'Smoking',
                'Eventtime': eventtime,
                'EventPic': eventpic
            }
            data_dict['contentLength'] = len(str(data_dict))+13+10
            json_data = json.dumps(data_dict)
            self.rq.lpush(self.TaskID, json_data)
            print("吸烟事件", sw_ret)
        elif sw_ret=={}:
            print("应该是出现了错误，没有找到图片")
        else:
            print("未检测到吸烟现象")
    
    def face_event(self):
        print("员工离岗事件在逻辑上存在问题,在人脸检测中已有解释")
        pass

    def run(self):
        while True:
            # 查看event_setting
            data_event = {}
            data = {}
            with open(gParam.Event_Setting_Json) as f:
                data_event = json.load(f)
            time.sleep(0.02)
            with open(gParam.Setting_Json) as f:
                data = json.load(f)
            if data['status'] == 'stop' or data_event['status'] == 'stop':
                # 等待识别完
                time.sleep(5)   
                # 将本地保存的视频流截图删除
                lists = os.listdir(gParam.VideoSplit_Path)
                lists.sort(reverse=True, key=lambda fn: os.path.getmtime(gParam.VideoSplit_Path + "/" + fn))
                try:
                    for i in lists[10:]:
                        os.remove(os.path.join(gParam.VideoSplit_Path, i))
                    print("Event----清理冗余文件")
                except:
                    print("Event----无冗余文件")
                while self.rq.llen(self.TaskID)>0:
                    self.rq.rpop(self.TaskID)
                print('Event-----清理redis缓存成功')

                break
            if self.e_helmet:
                self.helmet_event()
            if self.e_smoking:
                self.smoking_event()
            if self.e_face:
                self.face_event()

            time.sleep(self.period)
        print("Event-----事件响应功能已关闭")
