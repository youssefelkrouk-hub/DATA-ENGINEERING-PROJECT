import os
import configparser


class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Chemin absolu basé sur l'emplacement de ce fichier, peu importe
        # depuis où le script est lancé
        base_dir = os.path.dirname(os.path.abspath(__file__))  # .../src/util
        self.CONFIG_PATH = os.path.join(base_dir, '..', 'config', 'config.ini')
        result = self.config.read(self.CONFIG_PATH, encoding='utf-8')
        if not result:
            raise FileNotFoundError(f"Config introuvable : {self.CONFIG_PATH}")

    def get_api_url(self):
        return self.config.get("API", 'url').strip()

    def get_input_dir(self):
        return self.config.get("Paths", 'input_dir').strip()

    def get_registry_file(self):
        return self.config.get("Paths", 'registry_file').strip()

    def get_output_dir(self):
        return self.config.get("Paths", 'output_dir').strip()

    def get_db_config(self):
        return {
            "host": self.config.get("Database", "host").strip(),
            "port": self.config.get("Database", "port").strip(),
            "dbname": self.config.get("Database", "dbname").strip(),
            "user": self.config.get("Database", "user").strip(),
            "password": self.config.get("Database", "password").strip(),
        }