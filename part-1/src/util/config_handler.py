import os
import configparser


class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Chemin absolu basé sur l'emplacement de ce fichier, peu importe
        # depuis où le script est lancé
        base_dir = os.path.dirname(os.path.abspath(__file__))  # .../src/util
        self.CONFIG_PATH = os.path.join(base_dir, '..', 'config', 'config.ini')

        result = self.config.read(self.CONFIG_PATH)
        if not result:
            raise FileNotFoundError(f"Config introuvable : {self.CONFIG_PATH}")

    def get_api_url(self):
        return self.config.get("API", 'url')

    def get_input_dir(self):
        return self.config.get("Paths", 'input_dir')

    def get_registry_file(self):
        return self.config.get("Paths", 'registry_file')