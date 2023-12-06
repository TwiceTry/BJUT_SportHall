import sys
import requests
import json
import re
import time
import random
import typing
import inspect

from dataclasses import dataclass, field
from urllib.parse import quote

import utils.Useragent as Useragent

from utils.log import HTMLFileStorage

# 匹配中文字符和常见标点符号的正则表达式
chinesePattern = r"\u4e00-\u9fff\u3000-\u303f\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65\u2022"

host: str = "http://wechartdemo.zckx.net"
# 一个可预约的账号openid，仅用来测试是否开放预约，会产生预约及取消记录
test_openid:str = "test openid"
# 设置 Fiddler 的代理地址和端口（默认端口为 8888）
fiddler_proxy = {
    "http": "http://192.168.5.155:8888",
    "https": "http://192.168.5.155:8888",
}
# 创建一个Session对象，并设置代理
requests = requests.Session()
requests.proxies.update(fiddler_proxy)


class SportUser(object):
    openidCollect: typing.Set['SportUser'] = set([])
    htmlFileSave = HTMLFileStorage('html/order')

    def __init__(self, openid: str):
        self.openid = openid
        if self.openid:
            self.info = self.getUserInfo()
            self.userName = self.info['userName']
            self.userPhone = self.info['userPhone']
            self.userIdentityNo = self.info['userIdentityNo']
            self.compusId = self.info['compus_id']

    def __str__(self):
        return self.openid

    def __repr__(self):
        return self.__str__()

    def __add__(self, other: str):
        return self.__str__() + other

    def __radd__(self, other: str):
        return other + self.__str__()

    def getMyOrder(self):
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(
            url=host+"/Ticket/MyOrder?openId="+self.openid, headers=fake_header)
        htmlFileSave.save_html(f'myorder__{self.openid[-8:]}.html', res.text)
        return res.text

    def cancelBook(self, orderNo):
        res = requests.post(url=host+"/Ticket/CancleOrder", data={"dataType": "json", "orderNo": str(orderNo)},
                            headers={'User-Agent': Useragent.random_one()})
        return json.loads(res.text)

    def getUserInfo(self):
        fake_header = {'User-Agent': Useragent.random_one()}
        info_url = host + "/Ticket/MySelf_Info?openId=" + self.openid
        res = requests.get(url=info_url, headers=fake_header)
        name = re.search(r"value=\"([\u4E00-\u9FFF]+)\"", res.text)
        phone_num = re.search(r"value=\"(\d{11})\"", res.text)
        people_id = re.search(r"value=\"(\d{17}\d|X)\"", res.text)
        compus_id = re.search(
            r"id=\"txtYKT_No\" value=\"([SB]?\d+)\"", res.text)
        return {'openid': self.openid, 'userName': name.group(1), "userPhone": phone_num.group(1),
                "userIdentityNo": people_id.group(1), "compus_id": compus_id.group(1)}

    @classmethod
    def getOrderInfo(cls, OrderId: str) -> dict:
        htmlFileName = f'order_{OrderId}.html'
        html_text = cls.htmlFileSave.get_html(htmlFileName)
        if not html_text:
            fake_header = {'User-Agent': Useragent.random_one()}
            info_url = host + f"/Ticket/Myticketinfo_N?orderNo={OrderId}"
            res = requests.get(url=info_url, headers=fake_header)
            html_text = res.text
            cls.htmlFileSave.save_html(htmlFileName, html_text)
        info = {}
        orderSportHall = re.search(
            fr'<!--预约时段-->\s+<div class="orderInfo_title2">\s+<h2>([\d{chinesePattern}]+)</h2>\s+</div>', html_text)
        if orderSportHall:
            info['Hall'] = orderSportHall.group(1)
        else:
            return info

        orderTitle = re.search(
            fr'<div class="orderInfo_title">\s+<p>\s+<span class="sp1">([{chinesePattern}]*)</span>\s+<span class="sp3">￥([\d\.]+)</span>\s+<span class="sp2">([{chinesePattern}]+)</span>\s+</p>\s+<div class="clear"></div>\s+</div>', html_text)
        # True if orderTitle.group(1) == '已取消' else False
        info['isCancelled'] = True if orderTitle.group(1) == '已取消' else False
        orderIsUsed = re.search(
            fr'<div class="orderInfo_title_time">\s+<p>([{chinesePattern}]+)</p>\s+</div>', html_text)
        # True if '已使用' in orderIsUsed.group(1) else False
        info['isUsed'] = True if '已使用' in orderIsUsed.group(1) else False
        
        orderDate = re.search(r'<td width="30%"><b>使用日期</b></td>\s+<td>\s+<p>(\d{4}-\d{2}-\d{2})</p>\s+</td>', html_text)
        info['useDate'] = orderDate.group(1)
        orderUserName = re.search(
            fr'<td width="30%"><b>出游人 1</b></td>\s+<td>\s+<p>([\&amp\;\#183\;{chinesePattern}\d\s\w]*)</p>\s+</td>', html_text)
        info['userName'] = orderUserName.group(1)
        orderUserPhoneNum = re.search(
            r"<td><b>手机号</b></td>\s+<td>\s+<p>([\d\*]+)</p>\s+</td>", html_text)
        info['phoneNum'] = orderUserPhoneNum.group(1)
        orderUserId = re.search(r"<td><b>身份证</b></td>\s+<td>\s+<p>([DT\w\d\*X]+)</p>\s+</td>", html_text)
        info['id'] = orderUserId.group(1)
        return info


day_type = typing.TypeVar('day_type', int, str)


Halls: typing.List['SportHall'] = []
htmlFileSave = HTMLFileStorage('html')


@dataclass
class SportHall:
    name: str
    projectNo: str
    reserveUrl: str
    openTime: str

    @classmethod
    def getHalls(cls) -> typing.List['SportHall']:
        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(url=host, headers=fake_header)
        res.encoding = 'utf-8'
        if res.text == '':
            raise ValueError
        re_str = r'<div class="style_info_right" onclick="goToReserve\((\d+),\'(\w*)\'\)">\s+<h3>([\u4E00-\u9FFF（）]+)</h3>\s+<h2><span class="spanD">(开放时间[\d：\:\-]+)</span></h2>'
        re_match = re.findall(re_str, res.text)
        for i in re_match:
            if i[2] not in ['羽毛球馆', '体育馆健身房', '乒乓球馆']:
                continue
            newone: 'SportHall' = cls(i[2],  # name
                                      i[0],  # projectNo
                                      i[1],  # reserveUrl
                                      i[3]  # openTime
                                      )
            if newone not in Halls:
                Halls.append(newone)
        return Halls.copy()
    
    testOpenId: SportUser = SportUser(test_openid)
        
    @classmethod
    def getHallByName(cls, name: str) -> typing.Union['SportHall', None]:
        if not len(Halls):
            cls.getHalls()
        for i in Halls:
            if name in i.name:
                return i
        return None

    @classmethod
    def getNewOrderId(cls) -> str:
        gymHall = cls.getHallByName('体育馆健身房')  # 不限流，故可测试是否开放预约
        target_date = gymHall.day2date(-1)

        target_date_time_info = gymHall.getValidTimeInfo(target_date)
        filterList = gymHall.filterTimeInfo([12,], target_date_time_info)

        testTimeItem = random.choice(filterList)
        try:
            res = gymHall.bootIt(target_date, testTimeItem, cls.testOpenId.info)
        except:
            return ''
        if res['result']:
            cls.testOpenId.cancelBook(res['book_id'])
            return res['book_id']
        else:
            return ''

    @classmethod
    def testOrder(cls) -> bool:
        return bool(cls.getNewOrderId())

    def __post_init__(self):
        self.dayPlaceTime: dict = {}
        self.places: dict = {}
        self.hours: list = []
        self.dataSample: dict = {}

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    
    @property
    def url(self) -> str:
        address = "SportHallsKO"
        if self.reserveUrl == '':
            address = "Ticket"
        l_url = host + "/Ticket/" + address + \
            "?projectNo=" + self.projectNo + "&openId=" + self.testOpenId
        return l_url

    @property
    def body(self) -> str:
        name = "__pre"+inspect.currentframe().f_code.co_name
        if hasattr(self, name):
            return self.__getattribute__(name)

        fake_header = {'User-Agent': Useragent.random_one()}
        res = requests.get(url=self.url, headers=fake_header)
        res.encoding = "utf-8"
        self.places = {}
        if self.reserveUrl == '':
            self.dataSample = {}
        else:
            re_str = r'{&quot;STYLENAME&quot;:&quot;(?:(?:(\d+)号(?:场地|球台))|(?:乒乓球(\d+)))&quot;,&quot;STYLENO&quot;:(\d+)}'
            places = re.findall(re_str, res.text)
            if len(places):
                for i in range(len(places)):
                    places[i] = list(places[i])
                    places[i].remove("")
                    places[i] = [places[i][1], places[i][0]]
                places = dict(places)  # ["styNo","场地号"]

            hours = re.findall(
                r"<li(?: style=\"\")?>(\d+:\d+) —</li>", res.text)
            self.dataSample = {}
            for place in places.keys():
                self.dataSample[place] = {}
                for hour in hours:
                    self.dataSample[place][hour[:2]] = None
            self.places = places
            self.hours = hours

        self.__setattr__(name, res.text)
        saveFileName = f'{self.name}.html'
        htmlFileSave.save_html(saveFileName, res.text)

        return res.text

    @property
    def dateLimit(self) -> int:
        re_match = re.search(r'dayLimit = \"([\d])\";', self.body)
        return int(re_match.groups()[0])

    def day2date(self, day: day_type) -> str:
        if isinstance(day, str):
            if day == "-1":
                day = -1
            elif re.match(r"^\d{1,2}$", day):
                day = int(day)
            else:
                day_tuple = time.strptime(day, "%Y-%m-%d")
                today_tuple = time.localtime()
                day = day_tuple[2]-today_tuple[2]
        if isinstance(day, int):
            if day < 0:
                day = self.dateLimit
            if day > self.dateLimit:
                raise ValueError

        date = time.strftime(
            "%Y-%m-%d", time.localtime(time.time() + day * 3600 * 24))
        return date

    def getTimeInfo(self, day: day_type, f5=False, ValidTime=2):
        date = self.day2date(day)
        if (not f5) and date in self.dayPlaceTime.keys():
            if time.time() - self.dayPlaceTime[date]["info_time"] < ValidTime:
                return self.dayPlaceTime[date]["info"]

        re_match = re.findall(
            r"params\.data\.([\w]+) = [\"\']?([\d\w\_\,]+)[\"\']?;", self.body)
        re_match.pop()
        re_match = dict(re_match)

        post_data = re_match
        post_data['date'] = date
        res = requests.post(url=host + "/API/TicketHandler.ashx", data=post_data,
                            headers=Useragent.fake_headers()[0])
        res.encoding = 'utf-8'
        dict_info = json.loads(res.text)

        self.dayPlaceTime.update(
            {date: {'info':  dict_info, "info_time": time.time()}})

        return dict_info

    def getValidTimeInfo(self, day: day_type, f5=False) -> typing.List[dict]:
        dict_info = self.getTimeInfo(day=day, f5=f5)

        valid_list = []
        if self.reserveUrl == '':
            for i in dict_info['list']:
                if i['isCanReserve'] and i['restCount']:
                    valid_list.append(i)
        else:
            for hourTimeInfo in dict_info:
                for placeTimeInfo in hourTimeInfo['items']:
                    if set(placeTimeInfo.values()) != {0, '0'}:
                        valid_list.append(placeTimeInfo)

        return valid_list

    def filterTimeInfo(self, targetHours: typing.List[day_type], timeInfo: typing.List[dict]) -> typing.List[typing.List[dict]]:
        a = []
        targetHours = [str(i) for i in targetHours]
        target_date_time_info = timeInfo
        if len(self.reserveUrl):
            dictBystyNo: typing.Dict[str, typing.Dict[str, dict]] = {}
            for item in target_date_time_info:
                if item['styNo'] in dictBystyNo.keys():
                    dictBystyNo[item['styNo']].update({item['beginH']: item})
                else:
                    dictBystyNo.update({item['styNo']: {item['beginH']: item}})
            for styNo, hourItems in dictBystyNo.items():
                if set(targetHours) <= set(hourItems.keys()):
                    itemsList = []
                    for hour in targetHours:
                        itemsList.append(hourItems[hour])
                    a.append(itemsList.copy())

        else:
            for item in target_date_time_info:
                itemsList = []
                for hour in targetHours:
                    if hour in item['sTime']:
                        itemsList.append(item)
                a.append(itemsList.copy())

        return a

    def bootIt(self, target_date: str, orderItems: typing.List[dict], userInfo, result_list=None):

        if len(self.reserveUrl):
            timelist = []
            for time_dict in orderItems:
                timelist.append(
                    {
                        "minDate": time_dict["beginH"] + ":00",
                        "maxDate": str(int(time_dict["beginH"]) + 1) + ":00",
                        "strategy": time_dict['strId']
                    }
                )
        else:
            time_dict = orderItems[0]
            timelist = [{
                "minDate": time_dict['sTime'],
                "maxDate": time_dict['eTime'],
                "strategy": time_dict['id']
            }]

        re_match = re.search(
            r"var styleInfo\s=\s{(\r\n\s*\w+:\s'?[\w\d.]*'?,)+", self.body)
        re_match = re.findall(
            r"\r\n\s*(\w+):\s'?([\w\d.]*)'?,", re_match.group())
        styleInfolist = [{}]
        for i in re_match:
            styleInfolist[0][i[0]] = i[1]
        if styleInfolist[0]['styleNo'] == 'styleNo':
            styleInfolist[0]['styleNo'] = time_dict['styNo']
        styleInfolist[0]['ticketNum'] = 1

        userInfo.popitem()
        userInfo['userName'] = quote(userInfo['userName'].replace('·', ' '))
        userInfoList = [userInfo]
        post_data = {
            "dataType": "json",
            "orderJson": json.dumps({
                "userDate": self.day2date(target_date),
                "timeList": timelist,
                "totalprice": 0,
                "styleInfoList": styleInfolist,
                "userInfoList": userInfoList,
                "openId": userInfo['openid'],
                "sellerNo": "weixin",
            })
        }

        res = requests.post(url=host + "/Ticket/SaveOrder", data=post_data,
                            headers={'User-Agent': Useragent.random_one()}, timeout=(3, 3)
                            )

        res_dict = json.loads(res.text)
        result = {}
        if res_dict:
            if "100000" in res_dict["Code"]:
                result = {
                    'result': True, 'message': res_dict["Message"], 'book_id': res_dict["Data"]}
            else:
                result = {'result': False,
                          'message': res_dict["Message"], 'book_id': ''}
        if not (result_list is None) and res_dict:
            result_list.append(result)
        return result


def bookTask(task):

    if isinstance(task.openid, str):
        task.openid = SportUser(task.openid)
    if task.openid not in SportUser.openidCollect:
        SportUser.openidCollect.add(task.openid)
    if isinstance(task.Hall, str):
        task.Hall = SportHall.getHallByName(task.Hall)

    res_list = []
    testTimes = 5
    for i in range(testTimes):
        res = SportHall.testOrder()
        if res:
            break
    if i == testTimes-1:
        res_list.append(f'testTimes is {i}')


    timeInfo = task.Hall.getValidTimeInfo(task.target_date)

    a = task.Hall.filterTimeInfo(task.target_time, timeInfo)
    if len(a):
        res = task.Hall.bootIt(
            task.target_date, random.choice(a), task.openid.info, result_list=res_list)

    task.result = res_list
