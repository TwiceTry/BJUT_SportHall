import sys
import requests
import json
import re
import time
import random
import typing
import Useragent
from urllib.parse import quote
from threading import Timer

start = time.time()

class SportUser(object):
    host_url = "http://wechartdemo.zckx.net"
    def __init__(self,openid):
        self.openid=openid
        self.info = self.get_user_info()
        self.userName = self.info['userName']
        self.userPhone = self.info['userPhone']
        self.userIdentityNo = self.info['userIdentityNo']
        self.compusid = self.info['compus_id']

    def __str__(self):
        return self.openid
    def __repr__(self):
        return self.openid

    def get_myorder(self):
        fake_header = {'User-Agent': Useragent.random_one()}
        res=requests.get(url=self.host_url+"t/Ticket/MyOrder?openId="+self.openid,headers=fake_header)

    def get_user_info(self):
        fake_header = {'User-Agent': Useragent.random_one()}
        info_url = self.host_url + "/Ticket/MySelf_Info?openId=" + self.openid
        res = requests.get(url=info_url, headers=fake_header)
        name = re.search(r"value=\"([\u4E00-\u9FFF]+)\"", res.text)
        phone_num = re.search(r"value=\"(\d{11})\"", res.text)
        people_id = re.search(r"value=\"(\d{17}\d|X)\"", res.text)
        compus_id = re.search(r"id=\"txtYKT_No\" value=\"([SB]?\d+)\"", res.text)
        return {'openid':self.openid,'userName': name.group(1), "userPhone": phone_num.group(1),
                "userIdentityNo": people_id.group(1),"compus_id": compus_id.group(1)}


day_type = typing.TypeVar('day_type',int,str)
class SportHall(object):
    openid_list = [
                   ]
    host_url = "http://wechartdemo.zckx.net"
    Halls_list = []

    @classmethod
    def get_Halls(cls):
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(url=cls.host_url, headers=fake_header)
        res.encoding = 'utf-8'
        if res.text == '':
            raise ValueError
        re_str = r'<div  class="style_info_right" onclick="goToReserve\((\d+),\'(\w*)\'\)">\s+<h3>([\u4E00-\u9FFF]+)</h3>\s+<h2><span class="spanD">(开放时间：[\d\:\-]+)</span></h2>'
        re_match = re.findall(re_str, res.text.replace('\n', ''))
        for i in re_match:
            newone=SportHall({'projectNo': i[0], 'reserveUrl': i[1], 'name': i[2], 'time': i[3]})
            if newone not in cls.Halls_list:
                cls.Halls_list.append(newone)
        return cls.Halls_list.copy()


    @classmethod
    def get_Hallbyname(cls,name):
        if not len(cls.Halls_list):
            cls.get_Halls()
        for i in cls.Halls_list:
            if name in i.name:
                return i
        return False

    @classmethod
    def boot_it(cls,Hall,target_date,info,openid_info,result_list=None):
        time_dict = info
        re_match = re.search(r"var styleInfo\s=\s{(\r\n\s*\w+:\s'?[\w\d.]*'?,)+", Hall.body)
        re_match = re.findall(r"\r\n\s*(\w+):\s'?([\w\d.]*)'?,", re_match.group())
        user_info = openid_info
        user_info.popitem()
        styleInfolist = [{}]
        for i in re_match:
            styleInfolist[0][i[0]] = i[1]
        if styleInfolist[0]['styleNo'] == 'styleNo':
            styleInfolist[0]['styleNo'] = time_dict['styNo']
        styleInfolist[0]['ticketNum'] = 1
        if len(Hall.reserveUrl):
            timelist = [{
                "minDate": time_dict["beginH"] + ":00",
                "maxDate": str(int(time_dict["beginH"]) + 1) + ":00",
                "strategy": time_dict['strId']
            }]
        else:
            timelist = [{
                "minDate": time_dict['sTime'],
                "maxDate": time_dict['eTime'],
                "strategy": time_dict['id']
            }]

        user_info['userName'] = quote(user_info['userName'])
        userInfoList = [user_info]
        post_data = {
            "dataType": "json",
            "orderJson": str(
                {
                    "userDate": target_date,
                    "timeList": timelist,
                    "totalprice": 0,
                    "styleInfoList": styleInfolist,
                    "userInfoList": userInfoList,
                    "openId": user_info['openid'],
                    "sellerNo": "weixin",
                }
            )
        }

        res = requests.post(url=cls.host_url + "/Ticket/SaveOrder", data=post_data,
                            headers={'User-Agent': Useragent.random_one()},
                            )
        res_dict = json.loads(res.text)
        result = {}
        if res_dict:
            if "100000" in res_dict["Code"]:
                result = {'result': True, 'message': res_dict["Message"], 'book_id': res_dict["Data"]}
            else:
                result = {'result': False, 'message': res_dict["Message"], 'book_id': ''}
        if not (result_list is None) and res_dict:
            result_list.append(result)
        return result

    @classmethod
    def book_task(cls, task):
        if task.openid not in cls.openid_list:
            cls.openid_list.append(task.openid)
        if isinstance(task.Hall,str):
            task.Hall=cls.get_Hallbyname(task.Hall)
        if isinstance(task.openid, str):
            task.openid=SportUser(task.openid)
        if int(task.target_date) != -1 :
            task.target_date=task.Hall.day2date(task.target_date)
        target_date_time_info=task.Hall.time_info(task.target_date)

        a=[]
        if len(task.Hall.reserveUrl):
            valid_list={}
            for place in target_date_time_info.keys():
                valid_list[place]={}
                for hour in target_date_time_info[place].keys():
                    if target_date_time_info[place][hour]:
                        valid_list[place][hour]=target_date_time_info[place][hour]
            for place in valid_list.keys():
                if set(task.target_time) <= set(valid_list[place].keys()):
                    for hour in task.target_time:
                        a.append(valid_list[place][hour])
                    break

        else:
            for hour in task.target_time:
                if hour in target_date_time_info.keys():
                    a.append(target_date_time_info[hour])

        user_info = task.openid.info
        res_list=[]
        """for i in a:
            res_list.append(cls.boot_it(Hall,Hall.day2date(task.target_date),i,user_info))
        """
        t_list=[]
        for i in a:
            t=Timer(0,cls.boot_it,(task.Hall,task.Hall.day2date(task.target_date),i,user_info,res_list))
            t.start()
            t_list.append(t)
        def countalive(t_list):
            count = 0
            for i in t_list:
                count += 1 if not i.is_alive() else 0
            return count
        while countalive(t_list) != len(a):
            time.sleep(1)
        task.result = res_list




    @classmethod
    def cancelBook(cls,orderNo):
        res=requests.post(url=cls.host_url+"/Ticket/CancleOrder",data={"dataType":"json","orderNo":str(orderNo)},
                          headers={'User-Agent': Useragent.random_one()})
        return json.loads(res.text)

    def __init__(self, dict_info:dict=None):
        if dict_info == None:
            dict_info={'name': '', 'projectNo': '', 'reserveUrl': '', 'time': ''}
        self.__dict__.update(dict_info)
        self.projectNo = dict_info['projectNo']
        self.reserveUrl = dict_info['reserveUrl']
        self.name = dict_info['name']
        self.time = dict_info['time']
        self.day_place_time = {}
        self.places=None
        self.hours=None
        self.data_sample = None

    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name


    @property
    def openid(self):
        index = random.randint(0, len(self.openid_list) - 1)
        return self.openid_list[index]


    @property
    def url(self):
        address = "SportHallsKO"
        if self.reserveUrl == '':
            address = "Ticket"
        l_url = self.host_url + "/Ticket/" + address + "?projectNo=" + self.projectNo + "&openId=" + self.openid
        return l_url

    @property
    def body(self):
        name="__pre"+sys._getframe().f_code.co_name
        if hasattr(self,name):
            return self.__getattribute__(name)
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(url=self.url, headers=fake_header)
        res.encoding = "utf-8"
        self.places = {}
        if self.reserveUrl == '':
            self.data_sample= {}
        else:
            re_str=r'{&quot;STYLENAME&quot;:&quot;(?:(?:(\d+)号(?:场地|球台))|(?:乒乓球(\d+)))&quot;,&quot;STYLENO&quot;:(\d+)}'
            places = re.findall(re_str,res.text)
            if len(places):
                for i in range(len(places)):
                    places[i] =list(places[i])
                    places[i].remove("")
                    places[i]=[places[i][1],places[i][0]]
                places=dict(places)   #["styNo","场地号"]

            hours= re.findall(r"<li(?: style=\"\")?>(\d+:\d+) —</li>",res.text)
            self.data_sample= {}
            for place in places.keys():
                self.data_sample[place]={}
                for hour in hours:
                    self.data_sample[place][hour[:2]]=None
            self.places = places
            self.hours= hours
        self.__setattr__(name, res.text)
        return res.text

    @property
    def datelimit(self):
        re_match = re.search(r'dayLimit = \"([\d])\";', self.body)
        return int(re_match.groups()[0])

    def day2date(self, day):
        if isinstance(day,str):
            if day == "-1":
                day = -1
            elif re.match(r"^\d{1,2}$", day):
                day = int(day)
            else:
                day_tuple=time.strptime(day,"%Y-%m-%d")
                today_tuple=time.localtime()
                day=day_tuple[2]-today_tuple[2]
        if isinstance(day, int):
            if day < 0:
                day = self.datelimit
            if day > self.datelimit:
                raise ValueError

        date = time.strftime("%Y-%m-%d", time.localtime(time.time() + day * 3600 * 24))
        return date

    def time_info(self, day:day_type=-1,f5=False):

        date=self.day2date(day)
        if (not f5) and date in self.day_place_time.keys():
            if time.time() - self.day_place_time[date]["info_time"] <2:
                return self.day_place_time[date]["info"]

        re_match = re.findall(r"params\.data\.([\w]+) = [\"\']?([\d\w\_\,]+)[\"\']?;", self.body)
        re1 = []
        re2 = []
        for i in re_match:
            re1.append(i[0])
            re2.append(i[1])
        re_match = dict(zip(re1, re2))
        re_match.popitem()
        post_data = re_match
        post_data['date'] = date
        res = requests.post(url=self.host_url + "/API/TicketHandler.ashx", data=post_data,
                            headers=Useragent.fake_headers()[0])
        res.encoding = 'utf-8'
        dict_info = json.loads(res.text)
        this_day_data = self.data_sample.copy()
        alvi_list = []
        if self.reserveUrl == '':
            for i in dict_info['list']:
                if i['isCanReserve'] and i['restCount']:
                    this_day_data[i['sTime'][0:2]]=i
        else:
            for hour in dict_info:
                for place in hour['items']:
                    if set(place.values()) != {0, '0'}:
                        this_day_data[place['styNo']][place['beginH']]=place  #place['strId']

        self.day_place_time.update({date:{'info': this_day_data, "info_time":time.time()}})
        return this_day_data


if __name__ == "__main__":
    from prebook import Task, TaskOnTime
    aa=TaskOnTime()

    #@aa.preDeal
    def prdo():
        for i in SportHall.get_Halls():
            i.body
        for task in aa.__getattribute__('_' + aa.__class__.__name__ + '__tasklist'):
            task.Hall = SportHall.get_Hallbyname(task.Hall)
            task.openid = SportUser(task.openid)

    @aa.afterDone
    def afterdo():
        pass

    aa.doTask(SportHall.book_task)
    aa.run()

