import os
import csv
import requests
from datetime  import datetime
from util.config_handler import ConfigHandler



class ApiHandler:

    def __init__(self):
        self.config_handler=ConfigHandler()
        self.api_url=self.config_handler.get_api_url()
        self.input_dir=self.config_handler.get_input_dir()

    def get_data_to_csv(self):
        print("[INFO]: fetching new data... ")
        response=requests.get(self.api_url)
        if response.status_code==200:
            data=response.text
            #Generate filename with timestamp
            timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename=f"JOBS_v1_{timestamp}.csv"
            #save data to csv file
            file_path=os.path.join(self.input_dir,filename)
            with open(file_path,"w",newline="",encoding="utf-8") as csvfile:
                csvfile.write(data)
            print(f"[INFO]: data saved")
        else:
            print("Failed to fetch data from  API")

        