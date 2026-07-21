import os
import configparser
from util.exceptions import InvalidValueException


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

    def _get_value(self, section, option):
        """Centralise la lecture d'une valeur de config avec gestion d'erreurs.

        Toute lecture passe par ici, pour éviter de dupliquer les mêmes
        try/except dans chaque getter, et pour garantir qu'une valeur
        manquante ou vide lève toujours la même exception explicite.
        """
        try:
            value = self.config.get(section, option).strip()
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise InvalidValueException(
                f"Valeur de configuration manquante : [{section}] {option} ({e})"
            ) from e

        if not value:
            raise InvalidValueException(
                f"Valeur de configuration vide : [{section}] {option}"
            )

        return value

    def get_api_url(self):
        return self._get_value("API", "url")

    def get_input_dir(self):
        return self._get_value("Paths", "input_dir")

    def get_registry_file(self):
        return self._get_value("Paths", "registry_file")

    def get_output_dir(self):
        return self._get_value("Paths", "output_dir")

    def get_db_config(self):
        return {
            "host": self._get_value("Database", "host"),
            "port": self._get_value("Database", "port"),
            "dbname": self._get_value("Database", "dbname"),
            "user": self._get_value("Database", "user"),
            "password": self._get_value("Database", "password"),
        }
    