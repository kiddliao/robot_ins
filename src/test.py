# -*- coding: UTF-8 -*-
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
from event import Event
from facedetect import FaceDetect
from inspection import Inspection
from mongo.mongodb import features_write, person_write
from newthread import NewThread
from periodins import MultiObjects_yolov3
from stoppableThread import StoppableThread
from utils.utils import setting
from videocap import VCAP

# 由于Event事件响应功能接口仍未确定，因此初始化过程无法确定，目前初始化仅在测试时使用
# 初始化各线程  Event功能时的初始化
f_dectect = FaceDetect()
v_cap = VCAP()
v_cap.video_path = gParam.Video_Path
v_cap.video = '1.mp4'
# v_cap.video_path = False
# v_cap.start()
f_dectect.start()


setdefaulttimeout(10)

with open(gParam.Client_Server_Cfg, 'r') as f:
    configuration = json.loads(f.read())
    print('客户端与服务端TCP连接配置如下', configuration)

# redis 连接池
pool = redis.ConnectionPool(host=configuration['REDIS_HOST'],port=6379,
                            decode_responses=True)
r = redis.Redis(connection_pool=pool)

# 与服务端连接的配置
ADDR = (configuration['IP'],configuration['PORT'])
tctimeClient = socket(AF_INET,SOCK_STREAM)
tctimeClient.bind((configuration['LOCAL_IP'],5678))
tctimeClient.connect(ADDR)
BUFFSIZE = configuration['BUFFSIZE']


ins = Inspection(configuration['REDIS_HOST'])

def heartbeat():
    """心跳检测函数，根据configuration.txt中设置的间隔时间固定发出心跳检测，确认连接情况
    """
    while True:
        try:
            print('===============heartbeat start============')
            print('heart jinru 1')
            heartbeat = ins.register()
            tctimeClient.send(heartbeat.encode())
            print('done')
            ret_data = tctimeClient.recv(BUFFSIZE).decode()
            print('rt_register',ret_data)
            # tctimeClient.close()
            time.sleep(configuration['HEARTBEAT_INTERVAL'])
            print('============= heartbeat end ==========')
        except Exception as e:
            print('heartbeat error',e)

def event_ins():
    event = Event(e_helmet = True)
    event.TaskID = '10010-4396'
    v_cap.start()
    event.start()
    v_cap.video_path = False
    t_send = NewThread('Event', '10010-4396', 5, tctimeClient)
    t_send.period = 7

    # 开启事件响应功能 由于是测试 设置一分钟自动关闭
    setting(status='run', writing=True)
    setting(address=gParam.Event_Setting_Json, status='run', writing=True)

    t_send.start()

    time.sleep(60)
    setting(status='stop', writing=True)
    setting(address=gParam.Event_Setting_Json, status='stop', writing=True)

def functional():
    while True:
        time.sleep(2)
        try:
            json_data = ''
            while True:
                json_data_part = tctimeClient.recv(BUFFSIZE).decode('gbk')
                if '}]}' in json_data_part:
                    print("----------------------同步报文接收完毕")
                    json_data = json_data+json_data_part
                    break
                elif(len(json_data_part)<1000):
                    print("接收到了报文：^_^---")
                    json_data = json_data_part
                    break
                else:
                    print("===================同步报文未接收完毕")
                    json_data = json_data+json_data_part
                    pass
            # json_data = tctimeClient.recv(BUFFSIZE).decode('gbk')
            print('received functional data', json_data)
            if len(json_data)<10:
                print("json_data的长度小于10")
                continue
            try:
                json_data = json.loads(json_data.strip())
            except:
                print("无法解析发来的json_data")
                continue
            try:
                command = json_data['Command']
            except:
                print("无法查看发来json_data的命令是什么")
                continue
            if command == 'rt_register':
                print("rt_register-----------------")
                pass
            elif command == 'OPParas':
                """
                    由机器人平台向我们分析平台发送人为指定的参数，包括施工总人数，红帽人数（施工经理人数）、蓝帽人数、黄帽人数
                    如果是没有指定这些参数，需要我们设置一个默认值（这一点被原作者废弃）
                """
                print("----------------OPParas----------")
                TaskID = json_data['TaskID']
                # json.dumps()可以将字典转为字符串
                ins.set_opparas(json.dumps(json_data))
                rt_data = ins.rt_opparas(TaskID).encode()
                tctimeClient.send(rt_data)
                print('-------发送参数设置的即时相应报文完毕---------')
                continue
            elif command == 'Stop':
                """
                    根据接口协议，这个命令需要我们立刻停止当前分析工作，并返回响应
                """
                TaskID = json_data['TaskID']

                setting(status='stop', command='stop', writing=True)
                
                # 生成对应Stop命令的回传数据，默认一切正常
                rt_data = ins.rt_stop().encode()
                tctimeClient.send(rt_data)
                continue
            elif command == 'Inspection':
                """按照接口协议，发来的json串包含如下内容
                json:{
                    Command: "Inspection"
                    TaskID: string
                    InspecType: string, 123中的一个，分别对应立即,指定时间执行和取消之前的设置
                    InspecPeriod: int, 周期执行间隔
                    InspecStart: string, 指定开始时间
                    InspecEnd: string, 指定结束时间
                }
                希望我们有及时响应，判断是否正常执行；有异步响应，返回json串如下
                rt json:{
                    Command: "rt_Inspection"
                    TaskID: string
                    OpNumber: int, 施工总人数
                    OpRed: int, 红帽人数
                    OpBlue: int, 蓝帽人数
                    OpYellow: int, 黄帽人数
                    Image: string, 经标注过的图像, base64格式
                }
                """
                print('-----------Inspection-------------')
                TaskID = json_data['TaskID']
                print(ins.DataBase[TaskID])
                url = ins.DataBase[TaskID]['Url']

                # 先把即时响应返回去
                rt_data = ins.ack_inspection(TaskID).encode()
                tctimeClient.send(rt_data)
                print("Inspection 即时报文发送完毕")
                
                # 改addr，改属性，改status command
                setting(url=url, writing=True)

                if ins.DataBase[TaskID]['DeviceType']=='video':
                    v_cap.video_path = gParam.Video_Path
                    v_cap.video = '1.mp4'
                else:
                    v_cap.video_path = False

                # 首先根据发来的消息修改巡检设置和redis缓存key
                t_helmet.period = int(json_data['InspecPeriod'])
                t_helmet.name = json_data['TaskID']
                # 开始检测
                if json_data['InspecType']=="1" :
                    # 立即执行安全帽检测
                    setting(status='run', command='Inspection', writing=True)
                    # 创建线程，后台异步发送检测信息
                    ins_send = NewThread('Inspection', TaskID, int(json_data['InspecPeriod']), tctimeClient)
                    ins_send.start()
                elif json_data['InspecType']=="2":
                    # 修改周期巡检专属配置文件，添加TaskID
                    with open(gParam.PeriodIns_Setting_Json) as f:
                        status_periodins = json.load(f)
                    status_periodins[TaskID] = True
                    with open(gParam.PeriodIns_Setting_Json, 'w') as f: 
                        json.dump(status_periodins, f)
                    ins_settime = StoppableThread(TaskID, json_data['InspecStart'], json_data['InspecEnd'], json_data['InspecPeriod'], tctimeClient, url)
                    ins_settime.start()
                elif json_data['InspecType']=="3":
                    with open(gParam.PeriodIns_Setting_Json) as f:
                        status_periodins = json.load(f)
                    status_periodins.pop(TaskID)
                    print(TaskID, "该任务设置已取消")
                    with open(gParam.PeriodIns_Setting_Json, 'w') as f: 
                        json.dump(status_periodins, f)   
                else:
                    print("tcpclient出现了逻辑错误")
                continue

            elif command == 'SyncIdentify':
                """根据接口协议，这一步是为了同步照片库，身份信息
                传过来的是一个字符串数组
                PersonList:[
                    {
                        code: 工号， type: 职务, pic: base64格式的照片
                    }, {...}, {...}
                ]
                我们应做出及时响应
                """
                print('-----------SyncIdentify-------------')
                if type(json_data['PersonList'])==str:
                    person_data = eval(json_data['PersonList'])
                else:
                    person_data = json_data['PersonList']
                result = person_write(person_data)
                # features_write()
                ins.syncIdentify()
                rt_data = ins.rt_syncIdentify(ErrorCodeList=result)

                tctimeClient.send(rt_data.encode())
                continue
            elif command == 'StartIdentify':
                """根据接口协议，这一步要识别现场人员，然后不断的异步返回信息
                收到的json_data:{
                    Command: string, StartIdentify
                    TaskID: string
                    DeviceType: string, 设备类型，摄像头"camer"或者录像"recorder"
                    VideoType: string, 视频类型, "mp4"文件流或者"rtsp"实时流
                    IP: string, IP端口
                    Port: int, 端口
                    Url: string, URL地址
                    PersonCount: int, 需要识别出的人员个数
                    WaitMinutes: int, 最大等待时间
                }
                即时响应，看是否连接成功
                异步响应:
                json_data:{
                    Command: string, "rt_StartIdentify"
                    TaskID: string, 
                    Retval: string, "OK" or "Error"
                    MatchInfo: string, JSON格式的字符串, 当Retval=="OK"时才有
                    Reason: string, 错误原因
                    DismatchPic: string, 数据库没有但是现场有的人的图片
                }
                其中:
                    MatchInfo: "{
                        pic: base64, 识别时的截图
                        matches:[{
                            matchPic: base64, 照片库中的匹配照片
                            matchCode: string,
                            matchType: string,
                            matchPercent: int, 相似度   
                        }, {...}, {...}]
                    }"
                    Reason:"{
                        ErrorCode: string, 错误号
                        ErrorMessage: string, 出错原因
                    }"  
                """

                # 返回即时信息
                rt_data = ins.ack_startIdentify().encode()
                tctimeClient.send(rt_data)

                # 改addr， 改属性，改status command
                TaskID = json_data['TaskID']
                addr=json_data['Url']
                setting(url=addr, writing=True)

                # 具体类型的指定，接口文档说的很不清楚，需要进一步的考虑
                if json_data['VideoType']=='rtsp':
                    print("tcpclient-----使用rtsp流，有可能出现无效rtsp流现象，注意日志")
                    v_cap.video_path = False

                f_dectect.TaskID = TaskID
                f_dectect.time_limit = 60*int(json_data['WaitMinutes'])
                f_dectect.PersonCount = int(json_data['PersonCount'])
                f_dectect.period = 1


                setting(status='run', command='StartIdentify', writing=True)

                # 创建线程，后台异步发送人脸识别信息
                ins_send = NewThread(command='StartIdentify', 
                                    TaskID=TaskID, 
                                    period=4, 
                                    t_send=tctimeClient)
                ins_send.start()
            elif command == 'StopIdentify':
                setting(status='stop', command='StopIdentify', url='rtsp://admin:test1234@192.168.0.64/video1', writing=True)
                ins.StopIdentify()
                rt_data = ins.ack_stopidentify().encode()
                tctimeClient.send(rt_data)
                print("发送停止StopIdentify响应报文")
                continue
                
            else:
                pass
        except:
            print("这次没接收到指令")
            pass
        # 专为测试而生
        print("----------------------END-------------------")
        # break

def main():
    t = threading.Thread(target=heartbeat)
    t.start()
    t1 = threading.Thread(target=event_ins)
    t1.start()
    t2 = threading.Thread(target=functional)
    t2.start()

if __name__ == "__main__":
    main()
