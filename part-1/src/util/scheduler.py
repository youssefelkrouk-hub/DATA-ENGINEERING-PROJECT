import schedule
import time
from util.api_handler import ApiHandler
from util.file_handler import FileHandler

class Scheduler:
    def __init__(self):
        self.api_handler=ApiHandler()
        self.file_handler=FileHandler()
    def schedule_jobs(self):
        schedule.every(10).seconds.do(self.api_handler.get_data_to_csv)
        schedule.every(1).minutes.do(self.file_handler.track_new_files)

        while True:
            schedule.run_pending()
            time.sleep(1)
