# coding=utf-8
import base64
import colorsys
import json
import os
import sys
import threading
import time
from timeit import default_timer as timer

import redis
import socket

import gParam
import create_json as cj
from utils.utils import setting
from utils.utils import setting, read_queue, write_queue



class NewThread(threading.Thread):
    def __init__(self, command, TaskID, period, t_send):
        """本类建立的对象仅在setting_json做出一定的修改之后停止
            且不会主动修改setting_json文件
        args:
            command: string, 决定这个线程要做什么
            TaskID: string, 告知我们从那个redis缓存中提取信息
            period: int, 线程发送消息的周期
            t_send: socket.socket, 用来向服务端发送异步消息的连接
        """
        threading.Thread.__init__(self)
        self.command = command
        self.TaskID = TaskID
        self.period = period
        self.setting_json = gParam.Setting_Json
        self.t_send = t_send
        self.rq = redis.Redis(host='127.0.0.1', port=6379)

    def process_sw_ret(self, sw_ret):
        list = ['person', 'red', 'blue', 'yellow', 'white', 'head']
        OpNumber = 0
        # 将所有value都转为整形，没有就是0，并且计算人数
        for i in list:
            if i in sw_ret.keys():
                sw_ret[i] = int(sw_ret[i])
            else:
                sw_ret[i] = 0
            if i != 'person':
                OpNumber += sw_ret[i]
        OpNumber = max(sw_ret['person'], OpNumber)
        return sw_ret, OpNumber

    def rt_ins_helmet(self):
        print("newthread---------------------rt_ins_helmet-------")
        # 读取缓存信息，并进行相应处理
        print("newthread-----缓存长度", self.rq.llen(self.TaskID))
        if self.rq.llen(self.TaskID)==0:
            # print("newthread-----缓存中并无消息")
            return 
        while self.rq.llen(self.TaskID)>1:
            self.rq.rpop(self.TaskID)
        sw_ret = self.rq.lpop(self.TaskID).decode()
        sw_ret = json.loads(sw_ret)
        sw_ret, OpNumber = self.process_sw_ret(sw_ret)
        rt_data = cj.rt_Inspection(
                    TaskID=self.TaskID,
                    OpNumber=OpNumber,
                    OpRed=sw_ret['red'],
                    OpBlue=sw_ret['blue'],
                    OpYellow=sw_ret['yellow'],
                    OpWhite=sw_ret['white'],
                    OpNone=sw_ret['head'],
                    Image=sw_ret['file']
        )
        if type(rt_data)==str:
            rt_data = rt_data.encode()

        message_len = len(rt_data)
        print('newthread-----报文长度:', message_len)
        # message_len = cj.MessageLength(TaskID=self.TaskID, length=message_len)
        # self.t_send.send(message_len.encode())
        # # 防止报文长度发送在后
        # time.sleep(0.5)

        # # 建立报文发送队列间隔机制，读取发送队列，确定本消息发送时间
        # sleep_time = read_queue()
        # time.sleep(sleep_time)


        self.t_send.sendall(rt_data)
        print('newthread-----发送rt_data完毕')

        # # 发送完毕 修改发送队列
        # time.sleep(0.4)
        # write_queue()

        with open (gParam.Helmet_Log, 'ab') as f:
            f.write(rt_data)
        with open (gParam.Helmet_Log, 'a') as f:
            f.write('\n')
        # print('newthread-----发送 rt_ins_helmet 成功')

    def rt_face_dec(self):
        """人脸识别的报文遵循先进先出原则，所以采用lpush，rpop的方式
        """
        # 读取缓存信息
        print("newthread-----缓存长度", self.rq.llen(self.TaskID))
        if self.rq.llen(self.TaskID)==0:
            # print("newthread-----缓存中并无消息")
            return 
        # 人脸识别不能以这种方式来消除缓存 故注释掉
        # while self.rq.llen(self.TaskID)>1:
        #     self.rq.rpop(self.TaskID)
        rt_data = self.rq.rpop(self.TaskID)

        if type(rt_data)==str:
            rt_data = rt_data.encode()
        
        # message_len = len(rt_data)
        # message_len = cj.MessageLength(TaskID=self.TaskID, length=message_len)
        # self.t_send.send(message_len.encode())

        # # 防止报文长度发送在后
        # time.sleep(2)

        # # 建立报文发送队列间隔机制，读取发送队列，确定本消息发送时间
        # sleep_time = read_queue()
        # time.sleep(sleep_time)


        self.t_send.sendall(rt_data)
        print('newthread-----发送rt_data完毕')

        # # 发送完毕 修改发送队列
        # time.sleep(0.4)
        # write_queue()

        
        with open (gParam.Face_Detect_Log, 'ab') as f:
            f.write(rt_data)
        with open (gParam.Face_Detect_Log, 'a') as f:
            f.write('\n')


    def send_event(self):
        """采用lpush，rpop的方式
        """
        print("send event--------------------------------------------")
        # 读取缓存信息
        print("newthread-----缓存长度", self.rq.llen(self.TaskID))
        if self.rq.llen(self.TaskID)==0:
            return 
        rt_data = self.rq.rpop(self.TaskID)

        if type(rt_data) == str:
            rt_data = rt_data.encode()

        # message_len = len(rt_data)
        # print('newthread-----报文长度:', message_len)
        # message_len = cj.MessageLength(TaskID=self.TaskID, length=message_len)
        # self.t_send.send(message_len.encode())
        # # 防止报文长度发送在后
        # time.sleep(1.5)

        # # 建立报文发送队列间隔机制，读取发送队列，确定本消息发送时间
        # sleep_time = read_queue()
        # time.sleep(sleep_time)
        
        self.t_send.sendall(rt_data)
        
        # time.sleep(0.4)
        # write_queue()

        with open (gParam.Event_Log, 'ab') as f:
            f.write(rt_data)
        with open (gParam.Event_Log, 'a') as f:
            f.write('\n')
        print('newthread-----发送event_rt_data完毕')


    def send_test(self):
        self.t_send.send(b'wtx8887')

    def run(self):
        with open(self.setting_json) as f:
            data = json.load(f)
        cur_cmd = data['command']
        while True:
            with open(self.setting_json) as f:
                status = json.load(f)
                            
            print(self.command, '--------------------------------------------------')

            if status['status']=='run' and status['command']=='Inspection':
                if self.command == 'Inspection':
                    self.rt_ins_helmet()
                else:
                    print("newthread-----这个线程逻辑有错误")
            elif status['status']=='run' and status['command']=='StartIdentify':
                if self.command == 'StartIdentify':
                    self.rt_face_dec()
                else:
                    print("newthread-----这个线程逻辑有错误")
            elif status['status']=='run' and status['command']=='Test':
                self.send_test()
            elif status['status']=='run' and setting(gParam.Event_Setting_Json)['status']=='run' and self.command=='Event':
                self.send_event()
            elif status['status']=='stop' or cur_cmd != status['command']:
                print('newthread-----报文发送线程结束')
                break
            else:
                print("newthread-----又有逻辑漏洞")
            time.sleep(self.period/2.0)


