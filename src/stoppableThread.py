import threading
import json
import time
import gParam
from periodins import MultiObjects_yolov3
from utils.utils import setting
from newthread import NewThread

class StoppableThread(threading.Thread):

    def __init__(self, TaskID, starttime, endtime, period, t_send, url):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()
        self.ins_helmet = MultiObjects_yolov3('yolo')
        self.TaskID = TaskID
        self.starttime = starttime
        self.endtime = endtime
        self.period = period
        self.t_send = t_send
        self.url = url



    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            cur_time = time.time()
            with open(gParam.PeriodIns_Setting_Json) as f:
                status = json.load(f)
            if not self.TaskID in status.keys():
                break
            if cur_time < self.starttime:
                time.sleep(60)
            else: 
                self.ins_helmet.period = int(self.period)
                self.ins_helmet.name = self.TaskID
                
                setting(status='run', command='Inspection', url=self.url, writing=True)

                ins_send = NewThread('Inspection', self.TaskID, int(self.period), self.t_send)
                ins_send.start()
                while True:
                    cur_time = time.time()
                    if cur_time>self.endtime:
                        setting(status='stop', command='none', writing=True)
                        with open(gParam.PeriodIns_Setting_Json) as f:
                            status_periodins = json.load(f)
                        status_periodins.pop(self.TaskID)
                        print(self.TaskID, "该任务设置已取消")
                        with open(gParam.PeriodIns_Setting_Json, 'w') as f: 
                            json.dump(status_periodins, f)
                        break
                    else:
                        time.sleep(10)


        
        print("stoppableThread-----线程结束", self.TaskID)