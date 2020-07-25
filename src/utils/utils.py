# -*- coding: UTF-8 -*-

import json
import time
import gParam
def test():
    print("test successful")

def setting(address=gParam.Setting_Json, status='no', command='no', url='no', writing=False):
    """
    writing=False 时直接返回原配置
    writing=True 时只对指定的设置进行修改，其他的保持原状态
    args:
        address: string, setting_json的位置
        status: string, 要设置的状态
        command: string
        addr: string
        writing: bool, 决定是只读还是重写
    return:
        data: dict
    """
    with open(address) as f:
        data = json.load(f)
    if writing==False:
        return data
    else:
        if status != 'no':
            data['status'] = status
        if command != 'no':
            data['command'] = command
        if url != 'no':
            data['addr'] = url
        with open(address, 'w') as f:
            json.dump(data, f)
        return data

def read_queue():
    """我这里的逻辑是这样的，每个报文发送之前都调用此函数，然后n+=1，每个报文发送之后,等待400ms，都调用write_queue函数，n-=1。
    """
    n = 0
    with open('/Users/zhenchuansun/Documents/robot_ins/src/settings/send_queue.txt') as f:
        n = int(f.read())
    with open('/Users/zhenchuansun/Documents/robot_ins/src/settings/send_queue.txt', 'w') as f:
        f.write(str(n+1))
    return n*0.4

def write_queue():
    n = 0
    with open('/Users/zhenchuansun/Documents/robot_ins/src/settings/send_queue.txt') as f:
        n = int(f.read())
    if n==0:
        print("utils-----send_queue出现问题")
    with open('/Users/zhenchuansun/Documents/robot_ins/src/settings/send_queue.txt', 'w') as f:
        f.write(str(n-1))
    return n
