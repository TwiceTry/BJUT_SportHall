import random
import time
from sporthall import SportHall,Halls,SportUser

day = -1
stime = time.time()
SportUser.openidCollect.add(SportUser('oSkwT5XNsodPT_J9NgdFAuTHhnRo'))
SportHall.getHalls()
SportHall.testOrder()
etime = time.time()
print(etime - stime)
