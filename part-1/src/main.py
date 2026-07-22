from util.scheduler import Scheduler


def main():
    print("[INFO]: welcome to your Data Engineering 101 guide: \n")
    print(" press ctrl+c  to stop the process")
    scheduler = Scheduler()
    scheduler.schedule_jobs()


 
if __name__ == "__main__":
    main()