# -*- coding: UTF-8 -*-
import sys
sys.path.append('/home/face/faceRec/root/face_sdk/bin/')

import json
import os
import shutil

import threading
import time
import cv2
import redis

import gParam
# from faceRecognize import faceRecognize
from inspection import Inspection
from mongo.mongodb import base64_pic, features_abstract
from utils.utils import setting


class FaceDetect(threading.Thread):
    """
    从图片中捕捉到人脸，并进行识别
    整体的逻辑:
        每张截图与数据库中所有人脸比较，得到3个变量 finding，repeating，MatchInfo
        根据finding与repeating判断出 找到员工，重复找到员工，无匹配者三种情况并分别处理
        当超过规定时间时则发送相应报文，结束识别
    attr setting:
        self.time_limit: 设定时间限制
        self.period: 设定多长时间识别一张视频帧
        self.TaskID: 设定存入redis缓存的key
        self.PersonCount: 设定检测现场的人数
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.setting_json = gParam.Setting_Json
        self.videosplit_path = gParam.VideoSplit_Path

        self.face_path = gParam.Face_Path
        self.face_db = gParam.FaceDB_Path
        self.faceclipxml_path = gParam.FaceClipXml_Path

        # 以下这3个数据在一次StartIdentify事件或Sync之后要全部更新
        # face_datas中保存数据库中所有员工的信息列表，包括人脸特征
        # self.face_datas = features_abstract()
        # face_datas_flags是用来看有没有多次识别
        # self.face_datas_flags = [0]*len(self.face_datas)
        # person_num保存识别出员工的工号
        self.person_num = []

        # 本次识别的各种设定
        self.time_limit = 5
        self.period = 1
        self.TaskID = 'TaskID'
        self.PersonCount = 1

        self.rq = redis.Redis(host='127.0.0.1', port=6379)
        # 下面的是之前写的，应该不起作用
        with open(gParam.Client_Server_Cfg, 'r') as f:
            configuration = json.loads(f.read())
            # print('客户端与服务端TCP连接配置如下', configuration)
        self.ins = Inspection(configuration['REDIS_HOST'])
        

    def opencv_clip(self, frame, frame_name, xml):
        """
        args:
            frame: ndarray, 视频截图
            frame_name: 视频截图的绝对地址
            xml: str, 存放截取用配置文件
        returns: 
            facename_list: list, 存放脸的地址，没有脸则为[]
        """
        face_cascade = cv2.CascadeClassifier(xml)
        
        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray,1.3,5)
        facename_list = []
        name_time = time.time()
        if(len(faces)>0):
            for ind, (x,y,w,h) in enumerate(faces):
                img_part = frame[y:y+h,x:x+w]
                face_name = os.path.join(self.face_path,str(name_time)+str(ind)+'.jpg')
                cv2.imwrite(face_name, img_part)
                facename_list.append(face_name)
        #图片两张人脸的话face长度 一张人脸就长度为1吗？
        return facename_list

    def clip_face(self, frame_name):
        """从一张图片中截取下人脸部分
        args:
            frame_name: str, 视频流截图的绝对地址
        returns:
            facename_list: list, 存放截取的人脸图像的地址列表
        """
        xml = os.path.join(self.faceclipxml_path,'haarcascade_frontalface_default.xml')
        facename_list = []
        frame = cv2.imread(frame_name)
        
        facename_list = self.opencv_clip(frame, frame_name, xml)

        return facename_list

    def feature_compare(self, f1, f2):
        """
        args:
            f1: list, 存放截取图片的feature
            f2: list, 存放数据库人脸的feature
        returns:
            sum: float, f1与f2的相似度
        """
        sum = 0
        for ind, ele1 in enumerate(f1):
            ele2 = float(f2[ind])
            sum += float(ele1)*ele2 
        
        return sum 

    def face_identify(self, facename):
        """从face_db库中识别人脸
        args:
            facename: string, 存放截取出的人脸的地址
        returns:
            finding: bool, 有没有找到对应者
            repeating: bool, 找到的是不是重复者
            err_img_path: string, 存放未找到对应员工的图片的位置
            MatchInfo: dict, {pic: base64, 识别时的截图
                            matches:{
                                matchPic: base64, 照片库中的匹配照片
                                matchCode: string,
                                matchType: string,
                                matchPercent: int, 相似度   
                            }}
        """
        matches = []
        finding = False
        repeating = False
        err_img_path = facename

        # f1, self.face_datas, img_pic三花聚顶
        fr = faceRecognize()
        f1 = fr.get_feature(facename)
        img_pic = base64_pic(facename)

        # f1本来是二维的list
        try:
            f1=f1[0]
        except:
            # 利用一种不可能出现的逻辑情况做debug
            return False,True,err_img_path,b'wtx'

        n = 0
        for face_data in self.face_datas:
            f2 = face_data['feature']
            # f2本来是string
            f2 = eval(f2)
            matchType = face_data['type']
            similar = self.feature_compare(f1, f2)
            # print(".....................")
            # print("similarity...........")
            # print(similar)

            # 一般来讲一个图片就只会匹配到一个员工，但是也可能出现识别出多个相似度高的情况，
            # 此时就显示出matches的重要性了
            # 由于这里的逻辑完全无法走通，比如我可能匹配到很多人，但是我还要判断识别了多少人，这就是不可能的事情，所以说当有一张脸匹配到多张照片的时候，匹配到的多个身份全部认为到场，添加到person_num中！！！！！！！！！！！！！！！！！！！！！！！！！！
            if int(similar*100)>=60 and self.face_datas_flags[n]==0:
                finding = True
                self.person_num.append(face_data['code'])
                matchPic = base64_pic(face_data['pic'])
                match={
                    'matchPic':matchPic,
                    'matchCode':face_data['code'],
                    'matchType':matchType,
                    'matchPercent':similar,
                }
                matches.append(match)
                self.face_datas_flags[n] = 1
            elif int(similar*100)>=60 and self.face_datas_flags[n]!=0:
                finding = True
                repeating = True
            else:
                pass
            n += 1
        
        MatchInfo = {
            'pic': img_pic,
            'matches': matches
        }
        return finding, repeating, err_img_path, MatchInfo

    def update(self):
        """每次识别任务结束后都更新一下
        """
        self.face_datas = features_abstract()
        self.face_datas_flags = [0]*len(self.face_datas)
        self.person_num = []

    def detect_face(self):
        while True:
            status = {}
            with open(self.setting_json) as f:
                status = json.load(f)
            if status['status']=='run' and status['command']=='StartIdentify':
                start_time = time.time()
                person_count = 0
                
                while True:
                    # print("facedetect-----已经开启")
                    try:
                        """ 取出视频流的最新截图，从中截取人脸，保存人脸文件到gParam.Face_Path
                        """
                        lists = []
                        lists = os.listdir(self.videosplit_path)
                        try:
                            lists.sort(key=lambda fn: os.path.getmtime(os.path.join(self.videosplit_path,fn)))
                            # frame_name = os.path.join(self.videosplit_path, lists[-1])
                            frame_name = os.path.join(self.videosplit_path,"1581607991.216811.jpg")
                            
                        except:
                            frame_name = None
                            print('frame_name = None')
                        facename_list = self.clip_face(frame_name)
                        # time.sleep(0.3)
                        # print('frame_name:', frame_name)
                        # print('facename_list', facename_list)
                    except:
                        print("有错误")
                    
                    for facename in facename_list:
                        finding, repeating, err_img_path, MatchInfo = self.face_identify(facename)
                        # 根据返回信息决定如何发送报文
                        # 正常找到照片对应员工
                        if finding==True and repeating==False:
                            rt_data = {
                                'Command': 'rt_StartIdentify',
                                'TaskID': self.TaskID,
                                'Retval': 'OK',
                                'MatchInfo': json.dumps(MatchInfo)
                            }
                            rt_data = json.dumps(rt_data)
                            if type(rt_data)==str:
                                rt_data = rt_data.encode()
                            self.rq.lpush(self.TaskID, rt_data)
                            time.sleep(1)
                        # 没有找到与图片对应的数据库照片
                        elif finding==False and repeating==False:
                            reason = {
                                'ErrorCode':'0002',
                                'ErrorMessage':'find unmatched person'
                            }
                            rt_data = {
                                'Command': 'rt_StartIdentify',
                                'TaskID': self.TaskID,
                                'Retval': 'Error',
                                'Reason': json.dumps(reason),
                                'DismatchPic': MatchInfo['pic']
                            }
                            rt_data = json.dumps(rt_data)
                            if type(rt_data)==str:
                                rt_data = rt_data.encode()
                            self.rq.lpush(self.TaskID, rt_data)
                            time.sleep(1)
                        elif finding==False and repeating==True:
                            print('facedetect-----err_img_path---------',err_img_path)
                        else:
                            pass
                    
                    # 判断有没有超时
                    cur_time = time.time()
                    # print('time-----------------', cur_time-start_time)
                    if cur_time-start_time > self.time_limit: 
                        # 发送retval为error的报文，并主动停止
                        if self.person_num == []:
                            rt_data = self.ins.rt_startidentify(self.TaskID, Retval='Error', Reason='TimeOut')
                            if type(rt_data)==str:
                                rt_data = rt_data.encode()
                            self.rq.lpush(self.TaskID, rt_data)
                        else :
                            errormessage = 'just match ' + str(len(self.person_num))
                            reason = {
                                'ErrorCode':'0003',
                                'ErrorMessage':errormessage
                            }
                            rt_data = {
                                'Command': 'rt_StartIdentify',
                                'TaskID': self.TaskID,
                                'Retval': 'Error',
                                'Reason': json.dumps(reason)
                            }
                            rt_data = json.dumps(rt_data)
                            if type(rt_data)==str:
                                rt_data = rt_data.encode()
                            self.rq.lpush(self.TaskID, rt_data)
                        
                        print("facedetect-----time out! Stop!")
                        setting(status='stop', command='none', writing=True)
                    
                    with open(self.setting_json) as f:
                        data = json.load(f)
                    if not (data['status']=='run' and data['command']=='StartIdentify'):
                        print("facedetect-----停止人脸识别")
                        # 将本地文件中的截取的视频流图片删除，节省空间
                        lists = os.listdir(self.videosplit_path)
                        lists.sort(reverse=True, key=lambda fn: os.path.getmtime(self.videosplit_path + "/" + fn))
                        try:
                            for i in lists[3:]:
                                os.remove(os.path.join(self.videosplit_path, i))
                            print("facedetect-----清理冗余文件")
                        except:
                            print("facedetect-----无冗余文件")
                        while self.rq.llen(self.TaskID)>0:
                            self.rq.rpop(self.TaskID)
                        print('facedetect-----清理redis缓存成功')
                        self.update()
                        break
                    # 现在是根据这里的设定来决定多长时间截取一次人脸
                    time.sleep(self.period)
            else:
                print("facedetect-----未开启人脸识别")
                time.sleep(3)
            # break
 

    def run(self):
        self.detect_face()
if __name__=="__main__":
    cc=FaceDetect()
    cc.run()