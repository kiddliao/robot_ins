mongo/          数据库操作
yolo3/          目标检测模型
utils/          存放各种重复度较高的工具函数

settings/       存放控制各线程运转的setting_json文件

gParam.py       设置全局变量ss
inspection.py   根据参数生成格式适合的即时报文
create_json.py  生成报文用的工具函数

videocap.py     视频流截取线程类ss
facedetect.py   截取人脸，分析线程类ss
periodins.py    周期巡检，安全帽识别线程类
stoppableThread.py  周期巡检，设定巡检时间后开启的可自动按时结束，也可主动取消的线程类
event.py        事件响应线程类
smokingins.py   事件响应，吸烟检测类，通过事件响应线程调用类中方法
newthread.py    报文发送线程类，将redis队列中分析得到的消息用报文格式发送到服务端


tcpclient.py    运行时的主逻辑
test.py         每次单元测试时用来测试修改