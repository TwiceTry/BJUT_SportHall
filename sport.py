import requests
import json
import re
import time
import random
import Useragent
from urllib.parse import quote
from threading import Timer

class SportHall(object):
    host_url = "http://wechartdemo.zckx.net"
    openid = "" # 请填入一个openid, 只用来获取信息的id，不用来提交预约, 不填程序无法运行
    stime=9     # 每天预约开始时间，日后有变化可以修改
    etime=21    # 每天不可提交预约时间，在这个时间运行程序，程序会等到第二天可以预约的时候再开始
    # 任务字典的列表，type, keyword
    #               string, Hall, 运动场地名 
    #               string, target_date, 预约的日期，可使用 YYYY-MM-DD 格式 也可以用相对天数，不可为0，-1为默认为最新那天
    #               list, target_time, 预约起始时间的小时，HH格式, string类型的list
    #               string, openid, 提交预约的id，就是实际预约的账号
    task_list=[
                # 示例
                #{'Hall':"体育馆健身房",'target_date':"-1", 'target_time':['14',],'openid':'预约的openid'},
                #{'Hall':"羽毛球馆",'target_date':"2021-11-10", 'target_time':['13','14',],'openid':'预约的openid'},
                
               ]
    #
    def __repr__(self):
        return self.name
    def __init__(self,dict_info={'id':'','kind':'','name':'','time':''},openid=''):
        self.__dict__.update(dict_info)
        self.fake_header={'Usser-Agent':Useragent.random_one()}
        if openid != '':
            self.openid= openid
        self.place=None
        self.body=self.getbody()
        self.datelimit=self.getdatelimit()
    def url(self):
        projectNo= self.id
        if self.kind == '':
            reserveUrl = "Ticket"
        else:
            reserveUrl = "SportHallsKO"

        l_url = self.host_url + "/Ticket/" + reserveUrl + "?projectNo=" + projectNo + "&openId=" + self.openid
        return l_url
    def getbody(self):
        res = requests.get(url=self.url(),headers=self.fake_header)
        res.encoding="utf-8"
        if self.kind == '':
            pass
        else:
            place = re.findall(r'{&quot;STYLENAME&quot;:&quot;(\d+号(?:场地|球台))&quot;,&quot;STYLENO&quot;:(\d+)}',res.text)
            self.place=place
        return res.text
    def getdatelimit(self):
        re_match = re.search(r'dayLimit = \"([\d])\";',self.body)
        return int(re_match.groups()[0])
    def time_info(self,day=-1):
        if day <0:
            day = self.datelimit
        if day > self.datelimit:
            print("maxdata "+str(self.datelimit))
            day=self.datelimit
        re_match = re.findall(r"params\.data\.([\w]+) = [\"\']?([\d\w\_\,]+)[\"\']?;",self.body)
        re1=[]
        re2=[]
        for i in re_match:
            re1.append(i[0])
            re2.append(i[1])
        re_match=dict(zip(re1,re2))
        re_match.popitem()
        post_data =re_match
        date=time.strftime("%Y-%m-%d",time.localtime(time.time()+day*3600*24))
        post_data['date']= date
        res= requests.post(url=self.host_url+"/API/TicketHandler.ashx",data=post_data,headers=self.fake_header)
        res.encoding='utf-8'
        dict_info = json.loads(res.text)
        alvi_list=[]
        
        if self.kind == '':
            if len(dict_info['list']) == 0:
                return False
            if dict_info['list'][0]['isCanReserve'] and dict_info['list'][0]['restCount']:
                alvi_list.append(dict_info['list'][0])
        else:
            for hour in dict_info:
                for place in hour['items']:
                    if set(place.values()) != {0,'0'}:
                        alvi_list.append(place)
            if len(alvi_list) == 0:
                return False
        return {'Hall':self,'date':date,'List':alvi_list}

    @classmethod
    def home_page(cls,openid = ''):
        if openid == '':
            openid = cls.openid
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(url=cls.host_url+"/?openid="+openid,headers=fake_header)
        res.encoding='utf-8'
        return res.text

    @classmethod
    def get_Hallinfo_fromhome(cls,html_text='',openid = ''):
        if html_text =='':
            if openid == '':
                openid=cls.openid
            html_text = cls.home_page(openid)

        re_match = re.findall(r'<div  class="style_info_right" onclick="goToReserve\((\d+),\'(\w*)\'\)">\s+<h3>([\u4E00-\u9FFF]+)</h3>\s+<h2><span class="spanD">(开放时间：[\d\:\-]+)</span></h2>',html_text.replace('\n',''))
        Halls_dict=[]
        re_list={}
        for i in re_match:
            Halls_dict.append({'id':i[0],'kind':i[1],'name':i[2],'time':i[3]})
        for i in Halls_dict:
            Hall=SportHall(i)
            re_list.update({Hall.name:Hall})
        return re_list

    @classmethod
    def get_user_info(cls,openid=''):
        if openid=='':
            openid = cls.openid
        fake_header = {'User-Agent': Useragent.random_one()}
        info_url= cls.host_url+"/Ticket/MySelf_Info?openId="+openid
        res=requests.get(url=info_url,headers=fake_header)
        name = re.search(r"value=\"([\u4E00-\u9FFF]+)\"",res.text)
        phone_num = re.search(r"value=\"(\d{11})\"",res.text)
        people_id = re.search(r"value=\"(\d{17}\d|X)\"",res.text)
        compus_id = re.search(r"id=\"txtYKT\_No\" value=\"([SB]?\d{8,9})\"",res.text)
        return {'userName':name.group(1),"userPhone":phone_num.group(1),"userIdentityNo":people_id.group(1),"compus_id":compus_id.group(1)}

    @classmethod
    def book_it(cls,date,Hall,time_dict,openid):
        re_match=re.search(r"var styleInfo\s=\s{(\r\n\s*\w+:\s'?[\w\d.]*'?,)+",Hall.body)
        re_match=re.findall(r"\r\n\s*(\w+):\s'?([\w\d.]*)'?,",re_match.group())
        styleInfolist =[{}]
        for i in re_match:
            styleInfolist[0][i[0]]=i[1]
        if styleInfolist[0]['styleNo']=='styleNo':
            styleInfolist[0]['styleNo']=time_dict['styNo']
        styleInfolist[0]['ticketNum']=1
        if Hall.kind!='':
            timelist=[{
                "minDate": time_dict["beginH"]+":00",
                "maxDate": str(int(time_dict["beginH"])+1)+":00",
                "strategy": time_dict['strId']
            }]
        else:
            timelist = [{
                "minDate": time_dict['sTime'],
                "maxDate": time_dict['eTime'],
                "strategy": time_dict['id']
            }]
        user_info=cls.get_user_info(openid)
        user_info.popitem()
        user_info['userName'] = quote(user_info['userName'])
        userInfoList= [user_info]
        post_data={
            "dataType":"json",
            "orderJson":str(
                {
                    "userDate": date,
                    "timeList": timelist,
                    "totalprice": 0,
                    "styleInfoList": styleInfolist,
                    "userInfoList": userInfoList,
                    "openId": openid,
                    "sellerNo": "weixin",
                }
            )
        }
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.post(url=cls.host_url+"/Ticket/SaveOrder",data=post_data,headers=fake_header)
        if "成功" in json.loads(res.text)["Message"]:
            return True
        else:
            return False

    @staticmethod
    def find_time(avali_time_info,target_time=['18']):
        if not avali_time_info:
            return False
        re_list = []
        Hall=avali_time_info['Hall']
        for i in avali_time_info['List']:
            if Hall.kind =='':
                key_hour = 'sTime'
            else:
                key_hour = 'beginH'
            for j in target_time:
                if j in i[key_hour]:
                    re_list.append(i)
        if Hall.kind == '':
            pass
        else:
            line_dict={}
            line = set('')
            for i in re_list:
                line.add(i['styNo'])
            for i in list(line):
                line_dict[i]=[]
            for i in re_list:
                line_dict[i['styNo']].append(i)
            re_list=[]
            for i in line_dict.values():
                if len(i) == len(target_time):
                    re_list.append(i)
                    break
            if not len(re_list):
                for i in line_dict.values():
                    if len(i) == len(target_time)-1 and len(i)>0:
                        re_list.append(i)
                        break
        if len(re_list):
            return {'Hall':Hall,'date':avali_time_info['date'],'List':re_list[0]}
        else:
            return False
    @classmethod
    def book_task(cls, Hall,target_time,openid, day=-1):
        find_time_dict = cls.find_time(Hall.time_info(day), target_time=target_time)
        if find_time_dict:
            re_list=[]
            for book_time in find_time_dict:
                result = cls.book_it(find_time_dict['date'], find_time_dict['Hall'], book_time,openid)
                re_list.append((find_time_dict['date'], find_time_dict['Hall'], book_time))
            return re_list
        else:
            print("没有目标时间")
            return False
    @classmethod
    def run(cls):
        def task(relist,f,*args, **kwargs):
            relist.append(f(*args, **kwargs))

        if time.localtime().tm_hour >= cls.etime:
            now=list(tuple(time.localtime(time.time()+23*3600)))
        else:
            now=list(tuple(time.localtime()))
        now[3]=cls.stime
        now[4]=0
        now[5]=0
        target=time.mktime(tuple(now))
        print(time.asctime(time.localtime(target)),'target time',)
        Halls_dict = cls.get_Hallinfo_fromhome()
        while time.time() <= target:
            sec=target-time.time()
            if sec>30:
                time.sleep(sec/2)
            else:
                time.sleep(1)
        print(time.asctime(),"到点了",)
        re_list = []
        tlist=[]
        for i in cls.task_list:
            if len(i['target_date']) ==10:
                now=time.time()
                time_tuple=list(tuple(time.localtime(now)))
                time_tuple[0]=int(i['target_date'][0:4])
                time_tuple[1]=int(i['target_date'][5:7])
                time_tuple[2]=int(i['target_date'][8:10])
                target=time.mktime(tuple(time_tuple))
                day=round((target-now)/(24*3600))
                if day ==0:
                    print("预约今天的可能来不及")
                else:
                    i['target_date']=day
            else:
                i['target_date']=int(i['target_date'])
            t=Timer(0,task,(re_list,cls.book_task,Halls_dict[i['Hall']],i['target_time'],i['openid']), {"day":i['target_date']})
            tlist.append(t)
        for i in tlist:
            i.start()
            print(i.args[2:],i.kwargs)
        while len(re_list)!=len(cls.task_list):
            time.sleep(2)
        print(re_list)
        return re_list


if __name__ == "__main__":
    SportHall.run()

