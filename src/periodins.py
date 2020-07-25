# coding=utf-8
import base64
import colorsys
import json
import os
import sys
import threading
import time
from timeit import default_timer as timer

import cv2
import numpy as np
import redis
from keras import backend as K
from keras.layers import Input
from keras.models import load_model
from keras.utils import multi_gpu_model
from PIL import Image, ImageDraw, ImageFont

import gParam
from utils.utils import setting
from yolo3.model import tiny_yolo_body, yolo_body, yolo_eval
from yolo3.utils import letterbox_image


# 多目标检测，yolov3版
class MultiObjects_yolov3(threading.Thread):
    """从VideoSplit中找图片进行识别，将识别后绘制的图片保存到HelmetIns中，并
        将人数，安全帽等相应信息存入redis缓存
    attr setting:
        self.period: 设定多长时间识别一张视频帧
        self.name: 设定存入redis缓存的key，等同于其他类里的self.TaskID
    """
    _defaults = {
        "score" : 0.5,
        "iou" : 0.45,
        "model_image_size" : (416, 416),
        "gpu_num" : 0,
        "VOC_LABELS": {'none': (10, 'Background'),
                    'switcher0_0': (0, 'switcher0_0'),
                    'switcher0_1': (1, 'switcher0_1'),
                    'switcher1_0': (2, 'switcher1_0'),
                    'switcher1_1': (3, 'switcher1_1'),
                    'blue': (4, 'blue'),
                    'yellow': (5, 'yellow'),
                    'red': (6, 'red'),
                    'white': (7, 'white'),
                    'person': (8, 'person'),
                    'head': (9, 'head'),
                    }                  
    }

    @classmethod
    def get_defaults(cls, n):
        if n in cls._defaults:
            return cls._defaults[n]
        else:
            return "Unrecognized attribute name '" + n + "'"

    def __init__(self, h5_file, name='wtx'):
        """
        args: 
            h5_file: string, 权重的路径
            name: string, 决定了初始redis存放key值
            
            self.name: string, 决定了存放到redis缓存中时的key是什么,初始时设定默认值，根据机器人平台发来的消息再修改
            self.period: int, 检测周期值，初始时默认为2s
        """
        threading.Thread.__init__(self)
        K.clear_session()
        self.rq = redis.Redis(host='127.0.0.1', port=6379)
        self.name = name
        self.period = 2
        self.__dict__.update(self._defaults) # set up default values

        self.setting_path = gParam.Setting_Json
        self.videosplit_path = gParam.VideoSplit_Path
        self.helmet_ins_path = gParam.Helmet_Ins_Path

        self.classes_path = gParam.YOLO_Classes
        if 'tiny' in h5_file:
            self.model_path = gParam.YOLO_Tiny_Model
            self.anchors_path = gParam.YOLO_Tiny_Anchors
        else:
            self.model_path = gParam.YOLO_Model
            self.anchors_path = gParam.YOLO_Anchors
        self.class_names = self._get_class()
        self.anchors = self._get_anchors()
        self.sess = K.get_session()
        self.boxes, self.scores, self.classes = self.generate()

    def _get_class(self):
        classes_path = os.path.expanduser(self.classes_path)
        with open(classes_path) as f:
            class_names = f.readlines()
        class_names = [c.strip() for c in class_names]
        return class_names

    def _get_anchors(self):
        anchors_path = os.path.expanduser(self.anchors_path)
        with open(anchors_path) as f:
            anchors = f.readline()
        anchors = [float(x) for x in anchors.split(',')]
        return np.array(anchors).reshape(-1, 2)

    def generate(self):
        model_path = os.path.expanduser(self.model_path)
        assert model_path.endswith('.h5'), 'Keras model or weights must be a .h5 file.'

        # Load model, or construct model and load weights.
        num_anchors = len(self.anchors)
        num_classes = len(self.class_names)
        is_tiny_version = num_anchors==6 # default setting
        try:
            self.yolo_model = load_model(model_path, compile=False)
        except:
            self.yolo_model = tiny_yolo_body(Input(shape=(None,None,3)), num_anchors//2, num_classes) \
                if is_tiny_version else yolo_body(Input(shape=(None,None,3)), num_anchors//3, num_classes)
            self.yolo_model.load_weights(self.model_path) # make sure model, anchors and classes match
        else:
            assert self.yolo_model.layers[-1].output_shape[-1] == \
                num_anchors/len(self.yolo_model.output) * (num_classes + 5), \
                'Mismatch between model and given anchor and class sizes'

        print('{} model, anchors, and classes loaded.'.format(model_path))

        # Generate colors for drawing bounding boxes.
        hsv_tuples = [(x / len(self.class_names), 1., 1.)
                      for x in range(len(self.class_names))]
        self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self.colors = list(
            map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
                self.colors))
        np.random.seed(10101)  # Fixed seed for consistent colors across runs.
        np.random.shuffle(self.colors)  # Shuffle colors to decorrelate adjacent classes.
        np.random.seed(None)  # Reset seed to default.

        # Generate output tensor targets for filtered bounding boxes.
        self.input_image_shape = K.placeholder(shape=(2, ))
        if self.gpu_num>=2:
            self.yolo_model = multi_gpu_model(self.yolo_model, gpus=self.gpu_num)
        boxes, scores, classes = yolo_eval(self.yolo_model.output, self.anchors,
                len(self.class_names), self.input_image_shape,
                score_threshold=self.score, iou_threshold=self.iou)
        return boxes, scores, classes

    def detect_image(self, image):
        """
        利用yolov3网络对图片进行识别
        注意 对于cv2来说，h,w,channel = shape[0],shape[1],shape[2]
        args:
            image: ndarray
        returns:
            image: ndarray
            out_boxes: 
            out_scores:  
            out_classes: 

        """
        start = timer()
        if self.model_image_size != (None, None):
            assert self.model_image_size[0]%32 == 0, 'Multiples of 32 required'
            assert self.model_image_size[1]%32 == 0, 'Multiples of 32 required'
            boxed_image = letterbox_image(image, tuple(reversed(self.model_image_size)))
        else:
            # 这里也要改过来
            # new_image_size = (image.width - (image.width % 32),
            #                   image.height - (image.height % 32))
            new_image_size = (image.height-(image.height%32),
                                image.width-(image.width%32))
            boxed_image = letterbox_image(image, new_image_size)
        image_data = np.array(boxed_image, dtype='float32')

        image_data /= 255.
        image_data = np.expand_dims(image_data, 0)  # Add batch dimension.

        out_boxes, out_scores, out_classes = self.sess.run(
            [self.boxes, self.scores, self.classes],
            feed_dict={
                self.yolo_model.input: image_data,
                self.input_image_shape: [image.size[1], image.size[0]],
                # K.learning_phase(): 0
            })
        # return out_boxes, out_scores, out_classes
        font = ImageFont.truetype(font=os.path.join(gParam.Font_Path,'ARLRDBD.TTF'),
                    size=np.floor(2e-2 * image.size[1] + 0.5).astype('int32'))
        thickness = (image.size[0] + image.size[1]) // 600
        for i, c in reversed(list(enumerate(out_classes))):
            predicted_class = self.class_names[c]
            box = out_boxes[i]
            score = out_scores[i]

            label = '{} {:.2f}'.format(predicted_class, score)
            draw = ImageDraw.Draw(image)
            label_size = draw.textsize(label, font)

            top, left, bottom, right = box
            top = max(0, np.floor(top + 0.5).astype('int32'))
            left = max(0, np.floor(left + 0.5).astype('int32'))
            bottom = min(image.size[1], np.floor(bottom + 0.5).astype('int32'))
            right = min(image.size[0], np.floor(right + 0.5).astype('int32'))

            if top - label_size[1] >= 0:
                text_origin = np.array([left, top - label_size[1]])
            else:
                text_origin = np.array([left, top + 1])

            # My kingdom for a good redistributable image drawing library.
            for i in range(thickness):
                draw.rectangle(
                    [left + i, top + i, right - i, bottom - i],
                    outline=self.colors[c])
            draw.rectangle(
                [tuple(text_origin), tuple(text_origin + label_size)],
                fill=self.colors[c])
            draw.text(text_origin, label, fill=(0, 0, 0), font=font)
            del draw
        
        end = timer()
        # print('Time:', end-start)
        return image, out_boxes, out_scores, out_classes

    def getclass(self, index):
        for label in self.VOC_LABELS:
            if self.VOC_LABELS[label][0] == index:
                return label

    def detect_video(self):
        """detect_video的逻辑是这样的当我发现status:run，command:Inspection时
        我就调用这个来检查
            从截图目录下(videosplit_path)找到最新的一张图片，然后检测之，将对应内容放入redis缓存
            停止条件，setting_json中status和command发生变化
        """
        flag = 0
        while True:
            lists = os.listdir(self.videosplit_path)
            try:
                lists.sort(key=lambda fn: os.path.getmtime(self.videosplit_path + "/" + fn))
                frame = os.path.join(self.videosplit_path, lists[-1])
                # frame = os.path.join(self.videosplit_path,"1581607939.550507.jpg")
                frame = cv2.imread(frame)
                print("periodins----进入检测的图片为", lists[-1])
                
            except:
                frame = None

            if frame is None:
                time.sleep(1)
                if flag == 0:
                    flag = 1
                    continue
                else:
                    break
            else:
                flag = 0
            try:
                frame = np.array(frame).astype(np.int32)
                image = cv2.cvtColor(frame.astype('uint8'), cv2.COLOR_RGB2BGR)#严格说应该写BGR2RGB
                image = Image.fromarray(image).convert('RGB')
            except:
                print("periodins----bug")
                exit()
                continue

            image, rbboxes, rscores, rclasses = self.detect_image(image)
            sw_ret = {}

            for x in range(len(rclasses)):
                mclass = self.getclass(rclasses[x])
                if mclass in sw_ret.keys():
                    sw_ret[mclass] = sw_ret[mclass] + 1
                else:
                    sw_ret[mclass] = 1
            sw_ret['file'] = os.path.join(self.helmet_ins_path,str(lists[-1]))
            sw_ret['cam'] = str(lists[-1])

            sw_ret = json.dumps(sw_ret)
            # self.rq.lpush(self.name, sw_ret)
            vfile =os.path.join( self.helmet_ins_path+str(lists[-1]))

            # 缩小图片
            w, h = image.size
            image = image.resize((w//3, h//3), Image.ANTIALIAS)

            image.save(vfile)
            with open(self.setting_path) as f:
                data = json.load(f)
            if not (data['status']=='run' and data['command']=='Inspection'):
                break
            # 设定的巡检周期
            time.sleep(self.period)

    def event_detect_video(self):
        """event_detect_video的逻辑是这样的
            从截图目录下(videosplit_path)找到最新的一张图片，然后检测之，将检测结果返回
        returns:
            result: dict, 若未检测到图片则是空集合
        """
        lists = os.listdir(self.videosplit_path)
        try:
            lists.sort(key=lambda fn: os.path.getmtime(self.videosplit_path + "/" + fn))
            frame = os.path.join(self.videosplit_path, lists[-1])
            frame = cv2.imread(frame)
            print("periodins----进入检测的图片为", lists[-1])
            # for i in lists[4:-1]:
            #     os.remove(os.path.join(self.videosplit_path, lists[-1]))
            
        except:
            return '没有图片可以检测', {}

        try:
            frame = np.array(frame).astype(np.int32)
            image = cv2.cvtColor(frame.astype('uint8'), cv2.COLOR_RGB2BGR)
            image = Image.fromarray(image).convert('RGB')
        except:
            print("periodins----bug")

        image, rbboxes, rscores, rclasses = self.detect_image(image)
        sw_ret = {}

        for x in range(len(rclasses)):
            mclass = self.getclass(rclasses[x])
            if mclass in sw_ret.keys():
                sw_ret[mclass] = sw_ret[mclass] + 1
            else:
                sw_ret[mclass] = 1
        
        vfile = self.helmet_ins_path+str(lists[-1])
        sw_ret['file'] = vfile
        sw_ret['cam'] = str(lists[-1])

        image.save(vfile)
        return sw_ret

    def ins_period(self):
        while True:
            status = {}
            with open(self.setting_path) as f:
                status = json.load(f)
            # print('In periodins status: ', status)
            if status['status']=='run' and status['command']=='Inspection':
                # try:
                    self.detect_video()
                    with open(self.setting_path) as f:
                        data = json.load(f)
                    if not (data['status']=='run' and data['command']=='Inspection'):
                        # 等待识别完
                        time.sleep(1)
                        # 将本地存储的视频流截图删除，节省空间
                        lists = os.listdir(self.videosplit_path)
                        lists.sort(reverse=True, key=lambda fn: os.path.getmtime(self.videosplit_path + "/" + fn))
                        try:
                            for i in lists[3:]:
                                os.remove(os.path.join(self.videosplit_path, i))
                            print("periodins----清理冗余文件")
                        except:
                            print("periodins----无冗余文件")
                        while self.rq.llen(self.name)>0:
                            self.rq.rpop(self.name)
                        print('periodins----清理redis缓存成功')
                        # break
            else:
                print("periodins----没有收到检测安全帽的指令")
                time.sleep(3)

    def run(self):
        self.ins_period()

if __name__ == '__main__':
    # file=sys.argv[1]           #文件名
    # file='123.png'
    file='1581607939.550507.jpg'
    file_list=file.split('.')
    file_str='.'.join(file_list[:-1])
    if '/' in file_str:
        print(file_str)
        file_strs=file_str.split('/')
        print(file_strs)
        file_str=file_strs[-1]
    print(file_str)
    name = file_str        #队列名
    filename=file_str      #文件夹名

    # t2=CapVideo(file,name=name,filename=filename)
    # 安全帽模型

    t3 = MultiObjects_yolov3('./logs/darknet/yolov3-tiny.h5', name=name)
    
    t3.name = 'TEST TASK ID'
    t3.period = 3
    t3.run()
