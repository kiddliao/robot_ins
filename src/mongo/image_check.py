# -*- coding: utf-8 -*-
import io
from PIL import Image

#判断文件是否为有效（完整）的图片
#输入参数为文件路径
def IsValidImage(pathfile):
  bValid = True
  try:
    Image.open(pathfile).verify()
  except:
    bValid = False
  return bValid

#判断文件是否为有效（完整）的图片
#输入参数为bytes，如网络请求返回的二进制数据
def IsValidImage4Bytes(buf):
  bValid = True
  try:
    Image.open(io.BytesIO(buf)).verify()
  except:
    bValid = False
  return bValid

# 判断图片是否完整
def load_image(path):
    data=open(path,'rb+').read()
    bValid=IsValidImage4Bytes(data)
    return bValid
