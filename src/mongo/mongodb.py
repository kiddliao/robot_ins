# -*- coding: utf-8 -*-
import sys
sys.path.append('/home/face/faceRec/root/face_sdk/bin/')

import base64
import json
import time
import cv2
from random import choice

from pymongo import MongoClient

from mongo.image_check import load_image
from mongo.RedisQueue import RedisQueue
import gParam

# from faceRecognize import faceRecognize


def extract_feature(name):
    name=name.replace('.jpg','')
    path=gParam.FeatureData_Path+'{}.json'.format(name)
    with open(path) as f:
        data=json.load(f)
    feaure=data['feature']
    return feaure

# 信息录入
def person_write(informations):
    """将信息录入数据库, 注意这里的录入是把图片存到特定目录下，然后把其路径信息存到数据库中
    并且提取出图片的特征列表，一并放到数据库中
    args:
        informations: list, 列表中的每个元素包含着一个员工的全部信息（工号，职务，照片（base64格式））
    """
    client = MongoClient('127.0.0.1', 27017)
    coll = client.robot
    photo = coll.photo_info
    error_list = []
    for information in informations:
        if type(information)==str:
            information=eval(information)
        strs = information['pic']
        imgdata = base64.b64decode(strs)
        path = gParam.FaceDB_Path+'{}.jpg'.format(information['code'])
        file = open(path, 'wb')
        file.write(imgdata)
        file.close()

        # #这个地方可能要加一段代码来帮助我们截取出同步图像的人脸。从而只提取人脸的特征
        # xml = gParam.FaceClipXml_Path++'haarcascade_frontalface_default.xml'
        # frame = cv2.imread(path)
        # face_cascade = cv2.CascadeClassifier(xml)
        # gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        # faces = face_cascade.detectMultiScale(gray,1.3,5)
        # name_time = time.time()
        # if(len(faces)>0):
        #     for ind, (x,y,w,h) in enumerate(faces):
        #         img_part = frame[y:y+h,x:x+w]
        #         face_name = path
        #         cv2.imwrite(face_name, img_part)

        fr = faceRecognize()
        feature = fr.get_feature(path)
        try:
            feature = feature[0]
        except:
            print("this pic cannot get feature----------")
            continue

        # 判断图片是否完整
        result = load_image(path)
        if result == False:
            print("------------------此图片不完整--------")
            error_list.append(information['code'])

        data={
            'code':information['code'],
            'type':information['type'],
            'feature':str(feature),
            '_id':information['code'],
            'pic':'{}'.format(path)
        }
        total=photo.count({'code':data['code']})
        if total==0:
            photo.insert(data)
            print('员工工号'+data['code']+'数据已成功插入')
            time.sleep(1)
        if total==1:
            photo.update({'code':data['code']},{'$set':data})
            print('员工工号' + data['code'] + '数据已成功更新')
            time.sleep(1)
    client.close()
    print('人员信息录入完毕！')
    return error_list


# 特征提取录入
def features_write():
    """这里我决定作出修改，因为我私以为原来的程序就是扯淡
        将本函数去掉，将feature的提取部分写到之前的函数personwrite中
    """
    client = MongoClient('127.0.0.1', 27017)
    coll = client.robot
    photo = coll.photo_info
    q = RedisQueue('person')
    length=q.qsize()
    print('In features_write:', length)
    for i in range(int(length)):
        name=q.get().decode()
        print(name)

        fr = faceRecognize()
        feature = fr.get_feature(name)
        try:
            feature = feature[0]
        except:
            print("this pic cannot get feature")
            continue

        # 存入feature时，feature应该为str格式
        name=name.replace('.jpg','')
        infomation={
            'code':name,
            'feature':str(feature)
        }
        total = photo.count({'code': infomation['code']})
        if total==0:
            photo.insert(infomation)
            print('员工工号'+infomation['code']+'人脸特征数据已成功插入')
        if total==1:
            photo.update({'code':infomation['code']},{'$set':infomation})
            print('员工工号' + infomation['code'] + '人脸特征数据已成功更新')
    print('特征录入完毕！')
    client.close()

def features_abstract():
    client = MongoClient('127.0.0.1', 27017)
    coll = client.robot
    # 
    # feature = coll.Recognition
    feature = coll.photo_info
    feature_list=[]
    for i in feature.find({}):
        del i['_id']
        feature_list.append(i)

    print('数据库人脸特征提取完成！')
    return feature_list

def person_get(code):
    client = MongoClient('127.0.0.1', 27017)
    coll = client.robot
    photo = coll.photo_info
    for i in photo.find({'code':code}):
        del i['_id']
        return i
def base64_pic(path):
    """
    args:
        path: string, 图片路径
    returns:
        pic: base64格式图片
    """
    f = open(path, 'rb')
    pic = base64.b64encode(f.read()).decode()
    return pic


# lists=features_abstract()
# print(lists)

# client = MongoClient('127.0.0.1', 27017)
# coll = client.robot
# photo = coll.photo_info
#
# informations=[]
# for i in photo.find({}):
#     del i['_id']
#     informations.append(i)
# person_write(informations)
#
# start_time=time.time()
# features_write()
# end_time=time.time()
# print(end_time-start_time)
