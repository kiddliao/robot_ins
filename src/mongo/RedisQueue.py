# -*- coding: utf-8 -*-
import redis,json
import base64
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process,Pool


class RedisQueue(object):
    def __init__(self, name, namespace='queue',thread=1,process=1, **redis_kwargs):
        # 默认配置为host='localhost', port=6379, db=0
        # 默认单进程，单线程
        try:
            self.__db= redis.StrictRedis(**redis_kwargs)
            self.key = '%s:%s' %(namespace, name)

        except Exception as result:
            print(result)

    def qsize(self):
        # 返回当前队列长度
        try:
            return self.__db.llen(self.key)
        except Exception as result:
            print(result)

    def empty(self):
        # 检测当前队列是否为空
        try:
            return self.qsize() == 0
        except Exception as result:
            print(result)

    def put(self, item,priority=2):
        # 写入数据(单个）,优先级默认为2
        priority = int(priority)
        try:
            if priority==2:
                self.__db.rpush(self.key, item)
            elif priority==1:
                self.__db.lpush(self.key,item)
            else:
                print('priority参数格式错误！')
        except Exception as result:
            print(result)

    def putl(self, item,priority=2):
        # 写入数据(多个）,优先级默认为2
        priority = int(priority)
        try:
            for w_data in item:
                if priority==2:
                    self.__db.rpush(self.key, w_data)
                elif priority==1:
                    self.__db.lpush(self.key,w_data)
                else:
                    print('priority参数格式错误！')
                    break
        except Exception as result:
            print(result)

    # def lput(self,item,priority=2):
    #     # 写入数据(大量）,优先级默认为2,低于1w条无需使用
    #     p=Pool(self.max_process)
    #     num=int(len(item)/self.max_process)
    #     data=[item[i:i+3] for i in range(0,len(item),num)]
    #     p.map(self.thread,data)

    def lput(self,list,priority=2):

        pipe = self.__db.pipeline()
        priority=int(priority)
        if type(list)==str:
            list=eval(list)
        if priority == 1:
            for i in list:
                pipe.lpush(self.key,i)
        if priority == 2:
            for i in list:
                pipe.rpush(self.key,i)

        pipe.execute()

    def Rrange_all(self):
        #查看所有数据
        try:
            return self.__db.lrange(self.key,0,-1)
        except Exception as result:
            print(result)

    def Rrange(self,start,end):
        # 查看指定位置数据
        try:
            return self.__db.lrange(self.key,start,end)
        except Exception as result:
            print(result)

    def Rindex(self,index):
        # 通过位置，找出对应数据
        try:
            return self.__db.lindex(self.key,index)
        except Exception as result:
            print(result)

    def Rinsert(self,value,mode,item):
        # 两种模式：
        # 1. mode=1 ，value为位置索引（int）,在指定位置前插入
        # 2.mode=2，value为键值对，在指定键值对前插入
        try:
            if mode==1:
                data=self.__db.lindex(self.key,value)
                self.__db.linsert(self.key,data,item)
            elif mode==2:
                self.__db.linsert(self.key,value,item)
            else:
                print("mode参数格式错误")
        except Exception as result:
            print(result)

    def Rdel(self,value,count):
        # count > 0: 从头往尾移除值为 value 的元素。
        # count < 0: 从尾往头移除值为 value 的元素。
        # count = 0: 移除所有值为 value 的元素
        try:
            self.__db.lrem(self.key,count,value)
        except Exception as result:
            print(result)

    def Rdel_all(self):
        # 清空队列
        self.__db.ltrim(self.key,1,0)

    def get(self, block=True, timeout=None):
        # 取出并删除这条数据.
        #  如果参数block=True,timeout=None(为默认),则阻塞
        # 一直到有数据可取时
        try:
            if block:
                item = self.__db.blpop(self.key, timeout=timeout)
            else:
                item = self.__db.lpop(self.key)

            if item:
                item = item[1]
            return item
        except Exception as result:
            print(result)

    def get_all(self):
        try:
            length=self.__db.llen(self.key)
            # 第一种方法 pipline
            pipe = self.__db.pipeline()
            for i in range(int(length)):
                pipe.lpop(self.key)
            origin_data=pipe.execute()
            data=[]
            for w_data in origin_data:
                data.append(eval(w_data.decode('utf-8')))
            return data

        except Exception as result:
            print(result)

    def get_nowait(self):
        # 相当于get方法
        try:
            return self.get(False)
        except Exception as result:
            print(result)

    def scan(self):
        # 查看所有当前keys,及队列中数据数量
        result=[]
        name_list=self.__db.keys()
        for name in name_list:
            data = {}
            name_key=name.decode('utf-8')
            print(name_key)
            data['name']=name_key.replace('queue:','')
            data['length']=str(self.__db.llen(name_key))
            result.append(data)
        return result







