import os
import glob
import pandas as pd

from util.config_handler import ConfigHandler
from util.db_handler import DBHandler


def get_latest_csv(output_dir):
    """Récupère le fichier CSV le plus récent dans output_dir."""
    csv_files = glob.glob(os.path.join(output_dir, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Aucun fichier CSV trouvé dans {output_dir}")
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file


def main():
    config_handler = ConfigHandler()
    db_handler = DBHandler(config_handler)

    # 1. Trouver le dernier CSV nettoyé
    output_dir = config_handler.get_output_dir()
    latest_csv = get_latest_csv(output_dir)
    print(f"Chargement du fichier : {latest_csv}")

    # 2. Charger le CSV dans un DataFrame
    df = pd.read_csv(latest_csv, encoding="utf-8")

    # 3. Connexion à la base
    db_handler.connect()
    db_handler.create_table_if_not_exists()

    # 4. Upsert des données
    db_handler.upsert_dataframe(df, table_name="employees")

    # 5. Fermeture propre
    db_handler.close()
    print("Chargement terminé avec succès.")


if __name__ == "__main__":
    main()