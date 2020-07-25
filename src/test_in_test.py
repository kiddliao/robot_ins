import json
import os
import shutil
from socket import *
import threading
import time

import cv2
import redis

import gParam
from mongo.mongodb import person_write, features_write
from pymongo import *
from newthread import NewThread
from periodins import MultiObjects_yolov3
from utils.utils import setting
from facedetect import FaceDetect
from videocap import VCAP
from inspection import Inspection
from event import Event

# 为了方便测试先把各个线程都开一下
t_helmet = MultiObjects_yolov3('yolo')
f_dectect = FaceDetect()
v_cap = VCAP()
v_cap.video_path = gParam.Video_Path
v_cap.video = '1.mp4'
t_helmet.start()
v_cap.start()
f_dectect.start()

setdefaulttimeout(10)

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_respomses=True)
r = redis.Redis(connection_pool=pool)

ADDR = ('23.88.228.11', 43967)
tctimeClient = socket(AF_INET, SOCK_STREAM)
tctimeClient.connect(ADDR)
BUFFSIZE = 20480000

ins = Inspection('127.0.0.1')

def main():
    event = Event(e_smoking = True)
    event.TaskID = '4396'
    event.start()
    t_send = NewThread('Event', '4396', 4, tctimeClient)

    v_cap.video_path = gParam.Video_Path
    v_cap.video = 'smoking.mp4'

    setting(status='run', writing=True)
    setting(address=gParam.Event_Setting_Json, status='run', writing=True)

    t_send.start()

    time.sleep(30)
    setting(status='stop', writing=True)
    setting(address=gParam.Event_Setting_Json, status='stop', writing=True)


if __name__=="__main__":
    main()