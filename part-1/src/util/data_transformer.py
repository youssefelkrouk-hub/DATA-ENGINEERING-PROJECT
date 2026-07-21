import os
import glob
from datetime import datetime
import pandas as pd

from util.exceptions import FileHandlingException


class DataTransformer:
    def __init__(self, config_handler):
        self.config_handler = config_handler
        self.input_dir = self.config_handler.get_input_dir()
        self.output_dir = self.config_handler.get_output_dir()

    def _load_all_csv(self):
        pattern = os.path.join(self.input_dir, "*.csv")
        files = glob.glob(pattern)
        if not files:
            raise FileHandlingException(
                f"Aucun fichier CSV trouvé dans {self.input_dir}"
            )

        dataframes = []
        for f in files:
            try:
                dataframes.append(pd.read_csv(f))
            except (pd.errors.ParserError, UnicodeDecodeError, OSError) as e:
                # Un seul fichier corrompu/illisible ne doit pas arrêter tout
                # le pipeline silencieusement : on veut une erreur explicite
                # qui dit précisément quel fichier pose problème.
                raise FileHandlingException(
                    f"Impossible de lire le fichier {f} : {e}"
                ) from e

        try:
            merged = pd.concat(dataframes, ignore_index=True)
        except ValueError as e:
            # Peut survenir si les fichiers ont des colonnes totalement
            # incompatibles entre eux.
            raise FileHandlingException(
                f"Impossible de fusionner les fichiers CSV : {e}"
            ) from e

        print(f"{len(files)} fichiers fusionnés, {len(merged)} lignes au total")
        return merged

    def _clean(self, df):
        # 1. Doublons : basés sur 'id' si présent, sinon ligne entière
        before = len(df)
        if 'id' in df.columns:
            df = df.drop_duplicates(subset='id', keep='first')
        else:
            df = df.drop_duplicates()
        print(f"{before - len(df)} doublons supprimés")

        # 2. Nettoyer les espaces superflus sur les colonnes texte
        text_columns = df.select_dtypes(include='object').columns
        for col in text_columns:
            df[col] = df[col].astype(str).str.strip()

        # 3. Normaliser les formats
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower()
        if 'country_code' in df.columns:
            df['country_code'] = df['country_code'].str.upper()
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.capitalize()

        # 4. Valeurs manquantes
        df = df.replace(['', 'nan', 'NaN', 'None', 'none'], pd.NA)

        before = len(df)
        critical_cols = [c for c in ['id', 'email'] if c in df.columns]
        if critical_cols:
            df = df.dropna(subset=critical_cols)
        dropped = before - len(df)
        if dropped:
            print(f"{dropped} lignes supprimées (valeurs critiques manquantes)")

        df = df.fillna("Unknown")

        # 5. Types de données
        try:
            if 'years_experience' in df.columns:
                df['years_experience'] = pd.to_numeric(
                    df['years_experience'], errors='coerce'
                ).fillna(0).astype(int)
            if 'id' in df.columns:
                df['id'] = df['id'].astype(int)
        except (ValueError, TypeError) as e:
            raise FileHandlingException(
                f"Erreur lors de la conversion des types de données : {e}"
            ) from e

        return df.reset_index(drop=True)

    def transform_and_save(self):
        df = self._load_all_csv()

        if df.empty:
            raise FileHandlingException(
                "Le DataFrame fusionné est vide, rien à transformer."
            )

        df_clean = self._clean(df)

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = os.path.join(self.output_dir, f"JOBS_clean_{timestamp}.csv")
            df_clean.to_csv(output_path, index=False)
        except OSError as e:
            raise FileHandlingException(
                f"Impossible de sauvegarder le fichier nettoyé dans {self.output_dir} : {e}"
            ) from e

        print(f"Fichier nettoyé sauvegardé : {output_path} ({len(df_clean)} lignes)")
        return df_clean, output_path