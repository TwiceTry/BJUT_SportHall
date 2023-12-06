from sport.sporthall import SportHall, SportUser, bookTask
from utils.prebook import Task, TaskOnTime
if __name__ == "__main__":
    aa = TaskOnTime(etime=(0, 0, 0, 21, 30, 0, 0, 1, 0))

    @aa.preDeal
    def prdo(tasklist):
        for task in tasklist:
            SportUser.openidCollect.add(SportUser(task.openid))
            task.Hall = SportHall.getHallByName(task.Hall)
            task.Hall.body

    @aa.afterDone
    def afterdo():
        pass

    aa.doTask(bookTask)
    aa.run()
