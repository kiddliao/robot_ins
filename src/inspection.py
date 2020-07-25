import base64
import json
import time
import xml.etree.ElementTree as ET

import cv2
import redis

import create_json as cj


class Inspection(object):
    def __init__(self,redis_host):
        self.DataBase = {}
        # pool = redis.ConnectionPool(host=redis_host,
        #                             port=6379,decode_responses=True)
        # self.r = redis.Redis(connection_pool=pool)

    def register(self, RobotID='robot001', VisionID='vision001', user='hi', password='hello'):
        """按照接口协议发送心跳信号
        returns:
            json串:{
                Command: "Register"
                RobotID: string, 机器人编号
                VisionID: string, 视频分析系统ID
                user: string, 用户名
                password: string, 密码
            }
        """
        return cj.Register(RobotID, VisionID, user, password)

    def rt_opparas(self,TaskID, Retval='OK', Reason='NONE'):
        """这里我看接口协议里写的是在set_opparas执行后过一段时间再异步发送rt_opparas确定有没有出错等
        但是之前的人并没有按照接口来，而是准备自己额外定义事件响应类。
            因此这里直接返回一切正常的信号
        """
        return cj.rt_OPParas(TaskID, Retval, Reason)

    def rt_stop(self, Retval='OK', Reason='NONE'):
        """反正返回一切正常就完事了
        """
        return cj.rt_Stop(Retval, Reason)

    def ack_inspection(self, TaskID, Retval='OK', Reason='none'):
        return cj.ack_Inspection(TaskID, Retval, Reason)

    def set_opparas(self, json_data):
        '''
        这个可以这么做，整个inspection只有一个数据，即一个字典，这个字典的键是各个TaskID，而他的值
        则是所有OPParas里的数据。
        args:
            json_data: string, 机器人发来的json数据            
        '''
        # 说实话 原来的这三行代码把我看_了
        data_dict = json.loads(json_data)
        TaskID = data_dict['TaskID']
        self.DataBase[TaskID] = data_dict
        '''   
        self.OpStarttime = data_dict['OpStarttime']
        self.OpEndtime = data_dict['OpEndtime']
        self.OpNumber = data_dict['OpNumber']
        self.OpRed = data_dict['OpRed']
        self.OpBlue = data_dict['OpBlue']
        self.OpYellow = data_dict['OpYellow']
        self.OpBar = data_dict['OpBar']
        self.OpX = data_dict['OpX']
        self.OpY = data_dict['OpY']
        self.OpWidth = data_dict['OpWidth']
        self.OpHeight = data_dict['OpHeight']
        self.DeviceType = data_dict['DeviceType']
        self.VideoType = data_dict['VideoType']
        self.Ip = data_dict['Ip']
        self.Port = data_dict['Port']
        self.Url = data_dict['Url']
        self.TaskID = data_dict['TaskID']
        '''

    # def inspect(self,TaskID):
    #     '''
    #     vc = cv2.VideoCapture('test.mp4')
    #     c = 1
    #     if vc.isOpened():
    #         rval, frame = vc.read()
    #     else:
    #         rval = False
    #         frame = None
    #     vc.release()
    #     xml = intf.judge(frame)
    #     return xml
    #     '''
    #     time.sleep(1)
    #     return_json = self.r.lpop('sw_ret')
    #     print('return_json',return_json)
    #     ret_dict = json.loads(return_json)
    #     if ret_dict['TaskID'] == TaskID:
    #         with open('111.jpg', 'rb') as file:
    #             ret_dict['Image'] = base64.b64encode(file.read()).decode()
    #         return ret_dict
    #     else:
    #         ret_dict = {'OpRed':0,'OpBlue':2,'OpYellow':2,'OpWhite':0,'OpNone':0,'OpNumber':4,'TaskID':'123'}
    #         ret_dict['Image'] = 'fjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfdfjdlsfjdsljfldsjfldsjfldskjfdfd'
    #         return ret_dict


    def rt_inspect(self, TaskID, ret_dict):
        '''
        tree = ET.XML(xml)
        OpNumber = int(tree.find('OpNumber').text)
        OpRed = int(tree.find('OpRed').text)
        OpBlue = int(tree.find('OpBlue').text)
        OpYellow = int(tree.find('OpYellow').text)
        OpWhite = int(tree.find('OpWhite').text)
        OpNone = int(tree.find('OpNone').text)
        Image64 = str(tree.find('base64').text)
        '''
        OpNumber = ret_dict['OpNumber']
        OpRed = ret_dict['OpRed']
        try:
            OpBlue = ret_dict['OpBlue']
            OpYellow = ret_dict['OpYellow']
            OpWhite = ret_dict['OpWhite']
            OpNone = ret_dict['OpNone']
            Image64 = ret_dict['Image']
        except:
            OpBlue = 0
            OpYellow = 0
            OpWhite = 0
            OpNone = 0
            Image64 = ret_dict['Image']
        return cj.rt_Inspection(TaskID, OpNumber, OpRed, OpBlue, OpWhite, OpNone, OpYellow, Image64)

    def event(self, TaskID, ret_dict):
        '''
        tree = ET.XML(xml)
        OpNumber = int(tree.find('OpNumber').text)
        OpRed = int(tree.find('OpRed').text)
        OpBlue = int(tree.find('OpBlue').text)
        OpYellow = int(tree.find('OpYellow').text)
        Image64 = str(tree.find('base64').text)
        CrossFence = eval(tree.find('CrossFence').text)
        OffHelmet = eval(tree.find('OffHelmet').text)
        Smoking = eval(tree.find('Smoking').text)
        '''

        # OpNumber = ret_dict['OpNumber']
        # OpRed = ret_dict['OpRed']
        # #OpBlue = ret_dict['OpBlue']
        # #OpYellow = ret_dict['OpYellow']
        # Image64 = ret_dict['Image']
        # '''
        # CrossFence = ret_dict['CrossFence']
        # OffHelmet = ret_dict['OffHelmet']
        # Smoking = ret_dict['Smoking']
        # '''
        #
        # EventNumber = 1
        # Eventtime = time.time()
        # print(time.ctime())
        # EventPic = Image64
        # events = []
        # if int(OpNumber) < int(self.DataBase[TaskID]['OpNumber']):
        #     events.append(cj.Event(TaskID, EventNumber, 'OffDuty', Eventtime,
        #                            EventPic))
        # if int(OpRed) < int(self.DataBase[TaskID]['OpRed']):
        #     events.append(cj.Event(TaskID, EventNumber, 'MasterOff', Eventtime,
        #                            EventPic))
        '''
        if CrossFence:
            events.append(cj.Event(TaskID, EventNumber, 'CrossFence', Eventtime,
                                   EventPic))
        if OffHelmet:
            events.append(cj.Event(TaskID, EventNumber, 'OffHelmet', Eventtime,
                                   EventPic))
        if Smoking:
            events.append(cj.Event(TaskID, EventNumber, 'Smoking', Eventtime,
                                   EventPic))
        '''
        events=[ret_dict]
        return events

    def rt_syncIdentify(self, Retval='OK', ErrorCodeList='NONE', ErrorReasonList='NONE'):
        return cj.rt_SyncIdentity(Retval, ErrorCodeList, ErrorReasonList)

    def ack_startIdentify(self, Retval='OK', Reason='100'):
        return cj.ack_StartIdentify(Retval, Reason)

    def start_identify(self,r):
        pictures = []
        for picture in pictures:
            picture_feature = None
            max_sim = 0
            employee_features = r.lrange(0,-1)
            for i,employee_feature in enumerate(employee_features):
                sim = None
                if sim > max_sim:
                    max_sim = sim
                    index = i
            if max_sim>0.8:
                info = employee_features[index]



    def rt_startidentify(self, TaskID, Retval='OK', MatchInfo='matchinfo', Reason='None', DismatchPic='base64code'):
        return cj.rt_StartIdentify(TaskID, Retval, MatchInfo, Reason, DismatchPic)

    def ack_stopidentify(self, Retval='OK', Reason='None'):
        return cj.ack_StopIdentify(Retval, Reason)

    def syncIdentify(self):

        pass

    def StopIdentify(self):
        pass

    def stop(self,TaskID):
        pass
