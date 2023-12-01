import random
import time
from sporthall import SportHall,Halls,SportUser

day = -1
SportHall.getHalls()
stime = time.time()
hall = SportHall.getHallByName('体育馆健身房')
a=hall.filterTimeInfo([12],-1)
print(hall.day2date(hall.day2date(-1)))
for i in a:
    res=hall.bootIt(hall.day2date(-1),i,hall.getOpenid().getUserInfo())
    print(res)
etime = time.time()
print(etime - stime)
