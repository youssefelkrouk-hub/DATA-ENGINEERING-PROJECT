import os
from pathlib import Path

import configparser

class ConfigHandler:
    def __init__(self):
        self.config=configparser.ConfigParser()
        self.CONFIG_PATH="part-1/src/config/config.ini"
        self.config_read(self,self.CONFIG_PATH)
    def get_api_url(self):
        return self.config.get("API",'url')
    def get_input_dir(self):
        return self.config.get("PATHS",'input_dir')
    def get_registry_file(self):
        return self.config.get("Paths",'registry ')

