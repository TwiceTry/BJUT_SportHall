import random
import sys
import inspect
import json
import time
import pathlib
import log
import functools
from threading import Timer
import typing

class Task(object):
    def __init__(self, info_dict: dict):
        self.taskDict = info_dict
        self.result = {}

    def __eq__(self, other):
        if not isinstance(other,Task):
            return False
        return True if self.__dict__ == other.__dict__ else False

    @property
    def taskDict(self):
        for i in self.__taskDict.keys():
            item = self.__getattribute__(i)
            if isinstance(item, (typing.Dict,typing.List,typing.Tuple,str,int,float,bool)) or item is None:
                self.__taskDict[i]=str(item)
            else:
                self.__taskDict[i] = item
        return self.__taskDict

    @taskDict.setter
    def taskDict(self, dict1: dict):
        self.__taskDict = dict1
        for key in self.__taskDict.keys():
            self.__setattr__(str(key), self.__taskDict[key])

    @taskDict.deleter
    def taskDict(self):
        for key in self.__taskDict.keys():
            self.__delattr__(str(key))

    def __str__(self):
        return str({"Task": self.taskDict, "Result": self.result})

    def __repr__(self):
        return str({"Task": self.taskDict, "Result": self.result})

T = typing.TypeVar('T',typing.Dict,Task)

class TaskOnTime(object):
    def __init__(self, stime: tuple = (), etime: tuple = () , task_file_path='task.json'):
        self.log = None
        self.__tasklist = []
        self.setLogger()
        if len(stime) < 9:
            self.stime = (0, 0, 0, 7, 5, 0, 0, 1, 0)  # 预约开始时间，日后有变化可以修改
        if len(etime) < 9:
            self.etime = (0, 0, 0, 21, 30, 0, 0, 1, 0)  # 不可提交预约时间，在这个时间运行程序，程序会等到第二个预约周期再开始
        self.task_file_path = task_file_path
        self.readTask()
        self.timestep=3


    def __del__(self):
        self.writeTask()

    def readTask(self)->int:
        task_path = pathlib.Path(self.task_file_path)
        if not task_path.exists():
            task_path.write_text("[]")
        try:
            task_list = json.load(task_path.open(encoding='utf-8'))
        except:
            exit(0)
        for i in range(len(task_list)):
            task_list[i] = Task(task_list[i])
        for i in task_list:
            if task_list.count(i) > 1:
                task_list.remove(i)
        self.__tasklist = task_list
        return len(task_list)

    def addTask(self,dict_Task:T)->bool:
        if isinstance(dict_Task,typing.Dict):
            if not dict_Task in self.listTask():
                dict_Task=Task(dict_Task)
        if isinstance(dict_Task,Task):
            if not dict_Task in self.__tasklist:
                self.__tasklist.append(dict_Task)
            else:
                return False
        else:
            return False
        return True

    def delTask(self,dict_Task:Task)->bool:
        self.__tasklist.remove(Task)
        if dict_Task in  self.__tasklist:
            return False
        else:
            return True

    def listTask(self)->list:
        temp_list=[]
        for i in self.__tasklist:
            temp_list.append(i.taskDict)
        return temp_list

    def writeTask(self, temp_task_file_path='new_task.json'):
        temp_task_path = pathlib.Path(temp_task_file_path)
        body=self.listTask()
        for i in body:
            break
            i['active']=False
            for k in ['place']:
                if k not in i.keys():
                    i[k]=False
        try:
            json.dump(body,temp_task_path.open('w',encoding='utf-8'),ensure_ascii=False,indent=2)
        except:
            return
        task_path = pathlib.Path(self.task_file_path)
        task_path.unlink()
        temp_task_path.rename(self.task_file_path)




    def setLogger(self, *args, **kwargs):
        self.log = log.getlogger(*args, **kwargs)

    def mkTargetTime(self, timestamp=time.time()):
        target_time_tuple = self.stime
        end_time_tuple = self.etime
        now_time = list(tuple(time.localtime(timestamp)))
        day_or_week = target_time_tuple[7]
        target_time_tuple = list(target_time_tuple)
        for i in [0, 1, 2]:
            if target_time_tuple[i] == 0:
                target_time_tuple[i] = now_time[i]
        new_start_timestamp = time.mktime(tuple(target_time_tuple))
        end_time_tuple = list(end_time_tuple)
        for i in [0, 1, 2]:
            if end_time_tuple[i] == 0:
                end_time_tuple[i] = now_time[i]
        new_end_timestamp = time.mktime(tuple(end_time_tuple))
        if day_or_week == 0:  # 日无限制 打开周限制

            add = 7 if end_time_tuple[6] <= target_time_tuple[6] else 0
            end_time_tuple[6] += add
            now_time[6] += add
            add = 7 if end_time_tuple[6] < now_time[6] else 0
            end_time_tuple[6] += add
            target_time_tuple[6] += add
            delta1 = target_time_tuple[6] - now_time[6]
            delta2 = end_time_tuple[6] - now_time[6]
            new_start_timestamp += delta1 * 24 * 3600
            new_end_timestamp += delta2 * 24 * 3600
        else:
            delta1 = new_end_timestamp - timestamp
            # delta2 = timestamp - new_start_timestamp
            if delta1 < 0:
                new_start_timestamp += 24 * 3600
                new_end_timestamp += 24 * 3600
        if new_end_timestamp < new_start_timestamp:
            raise ValueError
        return new_start_timestamp, new_end_timestamp

    def __getobjname(self):
        for name, obj in globals().items():
            if self == obj:
                return name
        return self.__class__.__name__

    def __ifsetfunc(self,func):
        if func == None:
            self.log.warning("PLease use "+self.__getobjname()+"."+inspect.stack()[1][3] + " decorator")
            # sys.exit()
            return False
        return True

    def preDeal(self, func=None):
        if not func:
            self.log.info("You could use "+self.__getobjname()+"."+str(inspect.stack()[0][3]) + " decorator")
            return
        self.__ifsetfunc(func)

        @functools.wraps(func)
        def reback(*args,**kwargs):
            back=func(*args,**kwargs)
            return back
        self.__setattr__(sys._getframe().f_code.co_name,reback)
        # self.preDeal=reback
        return reback

    def doTask(self, func=None):  # 装饰函数 只有一个参数，Task对象
        tasklist=self.__tasklist
        @functools.wraps(func)
        def Multithreading():
            if not self.__ifsetfunc(func):
                return False
            self.log.info("任务开始执行")
            tlist = []
            for i in tasklist:
                t = Timer(0, func, (i,),)
                tlist.append(t)
                t.start()

            def countalive(t_list):
                count = 0
                for i in t_list:
                    count += 1 if not i.is_alive() else 0
                return count
            while countalive(tlist) != len(tasklist):
                time.sleep(1)
            for i in tasklist:
                self.log.info(i)
            return True
        self.__setattr__(sys._getframe().f_code.co_name,Multithreading)
        return Multithreading

    def afterDone(self, func=None):
        if not func:
            self.log.info("You could use "+self.__getobjname()+"."+str(inspect.stack()[0][3]) + " decorator")
            return
        self.__ifsetfunc(func)

        @functools.wraps(func)
        def reback(*args,**kwargs):
            back=func(*args,**kwargs)
            return back
        self.__setattr__(sys._getframe().f_code.co_name,reback)
        # self.preDeal=reback
        return reback

    @staticmethod
    def timeBlock(target):  # 阻塞
        while time.time() <= target:
            sec = target - time.time()
            time.sleep(sec / 2) if sec > 30 else time.sleep(2)

    def __runit(self):
        start_timestamp, end_timestamp = self.mkTargetTime()
        self.log.info('预约开始时间： ' + time.asctime(time.localtime(start_timestamp)))
        self.timeBlock(start_timestamp-60*5)
        self.preDeal()
        self.timeBlock(start_timestamp)
        self.log.info('预约时间已到')
        self.doTask()
        self.afterDone()
        self.log.info("执行结束")

    def run(self):
        self.__runit()


