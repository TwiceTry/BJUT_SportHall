import random
from sport.sporthall import SportHall, SportUser
from utils.prebook import Task, TaskOnTime
if __name__ == "__main__":
    aa = TaskOnTime(etime=(0, 0, 0, 21, 30, 0, 0, 1, 0))

    @aa.preDeal
    def prdo(tasklist):
        for task in tasklist:
            SportUser.openidCollect.add(SportUser(task.openid))
            task.Hall = SportHall.getHallByName(task.Hall)
            task.Hall.getTimeInfo(task.target_date)
            task.result = [
                f"successfully get target date: {task.Hall.day2date(task.target_date)} timeinfo "]

    @aa.afterDone
    def afterdo():
        pass

    @aa.doTask
    def bookTask(task):
        if isinstance(task.openid, str):
            task.openid = SportUser(task.openid)
        if task.openid not in SportUser.openidCollect:
            SportUser.openidCollect.add(task.openid)
        if isinstance(task.Hall, str):
            task.Hall: SportHall = SportHall.getHallByName(task.Hall)

        res_list = []
        timeInfo = task.Hall.getTimeInfo(task.target_date, ValidTime=5*60)
        timeInfo = task.Hall.getValidTimeInfo(
            task.target_date, timeInfo=timeInfo)
        if len(timeInfo) == 0:
            res_list.append(
                f"{SportHall.dateLimit(task.target_date)} has no timeInfo")
            return

        targetValidTimeInfo = task.Hall.filterTimeInfo(
            tuple(task.target_time), timeInfo)
        targetValidTimeInfo.reverse()
        testTimes = 0
        for targetTime in targetValidTimeInfo:
            fString = f"place:{task.Hall.places[targetTime[0]['styNo']]}, target hour:{task.target_time}"
            res_list.append(
                f"try {fString}")

            res = task.Hall.bootIt(
                task.target_date, targetTime, task.openid.info, result_list=res_list)
            testTimes += 1

            if res['result']:
                res_list.append(
                    f"successfully book  {fString}, orderId is {res['book_id']}")
                break
            else:
                res_list.append(
                    f"failed to  book {fString}")
        res_list.append(f'test book times is {testTimes}')
        task.result += res_list

    aa.run()
