import schedule
import time
from util.api_handler import ApiHandler
from util.file_handler import FileHandler
from util.exceptions import ProjectBaseException


class Scheduler:
    def __init__(self):
        self.api_handler = ApiHandler()
        self.file_handler = FileHandler()

    def _safe_run(self, job_func, job_name):
        """Exécute une tâche planifiée en isolant ses erreurs.

        Sans ce wrapper, une exception levée dans une tâche (ex: API en panne)
        remonterait jusqu'à schedule.run_pending() et ferait planter tout le
        `while True` du scheduler, y compris les autres tâches déjà planifiées.
        Ici, on attrape l'erreur, on la log, et on laisse le scheduler continuer
        pour retenter cette même tâche au prochain cycle.
        """
        try:
            job_func()
        except ProjectBaseException as e:
            print(f"[ERROR] La tâche '{job_name}' a échoué : {e}")
        except Exception as e:
            # Erreur inattendue, non prévue par nos exceptions custom :
            # on la log quand même au lieu de laisser planter le scheduler,
            # mais elle mérite d'être investiguée en priorité.
            print(f"[ERROR] Erreur inattendue dans la tâche '{job_name}' : {e}")

    def schedule_jobs(self):
        schedule.every(40).seconds.do(
            self._safe_run, self.api_handler.get_data_to_csv, "fetch_data_to_csv"
        )
        schedule.every(10).minutes.do(
            self._safe_run, self.file_handler.track_new_files, "track_new_files"
        )

        print("[INFO] Scheduler démarré.")
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                # Filet de sécurité ultime : même une erreur imprévue dans
                # schedule lui-même ne doit pas arrêter la boucle principale.
                print(f"[ERROR] Erreur inattendue dans la boucle du scheduler : {e}")
            time.sleep(1)