# BJUT_SportHall
A python3 program used to make an appointment for fixed time.
## 适用于北京工业大学 运动场地 小程序
sport.py 主要功能
Useragent.py 生成随机User-agent 字符串
## 使用条件
Python3 with requests
## 用法
按sport.py文件中提示修改添加openid,task_list
 #### 任务字典的列表，type, keyword
    #               string, Hall, 运动场地名 
    #               string, target_date, 预约的日期，可使用 YYYY-MM-DD 格式 也可以用相对天数，不可为0，-1为默认为最新那天
    #               list, target_time, 预约起始时间的小时，HH格式, string类型的list
    #               string, openid, 提交预约的id，就是实际预约的账号
运行后，会等到设置的时间开始预约
返回结果后程序结束
## 其他用法
##### linux 定时任务 
可以设置每天早上开始预约前一分钟运行
也可以再添加每隔固定时间运行
##### 会python的也可以在python程序中导入这个sport文件中的SportHall类

## End
写的烂，没注释，算是半成品吧，但是也不再写了
