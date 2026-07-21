import os
import csv
import time
import requests
from datetime import datetime
from util.config_handler import ConfigHandler
from util.exceptions import ApiRequestException

class ApiHandler:

    def __init__(self):
        self.config_handler = ConfigHandler()
        self.api_url = self.config_handler.get_api_url()
        self.input_dir = self.config_handler.get_input_dir()

    def get_data_to_csv(self):
        print("[INFO]: fetching new data using API.... ")

        start_time = time.perf_counter()
        try:
            response = requests.get(self.api_url, timeout=10)
        except requests.exceptions.RequestException as e:
            # Regroupe les erreurs réseau : timeout, DNS, connexion refusée, etc.
            raise ApiRequestException(
                f"Erreur réseau lors de l'appel à l'API : {e}"
            ) from e
        finally:
            elapsed_time = time.perf_counter() - start_time

        print(f"[INFO]: appel API terminé en {elapsed_time:.3f} secondes")

        if response.status_code != 200:
            raise ApiRequestException(
                f"Échec de l'appel API : code de statut {response.status_code} "
                f"reçu depuis {self.api_url}"
            )

        data = response.text

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"JOBS_v1_{timestamp}.csv"
        file_path = os.path.join(self.input_dir, filename)

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                csvfile.write(data)
        except OSError as e:
            # Erreur d'écriture disque : dossier inexistant, droits insuffisants, disque plein...
            raise ApiRequestException(
                f"Impossible d'écrire le fichier {file_path} : {e}"
            ) from e

        print(f"[INFO]: data saved -> {file_path}")