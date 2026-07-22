import psycopg2
from psycopg2.extras import execute_values

from util.exceptions import DBConnectionException, DBQueryException


class DBHandler:
    def __init__(self, config_handler):
        self.config_handler = config_handler
        self.conn = None

    def connect(self):
        db_config = self.config_handler.get_db_config()

        # Force l'encodage client pour éviter les soucis de décodage
        db_config["client_encoding"] = "utf8"

        try:
            self.conn = psycopg2.connect(**db_config)
        except UnicodeDecodeError as e:
            print("Erreur d'encodage dans les paramètres de connexion :")
            for k, v in db_config.items():
                print(f"  {k} -> {v!r}")
            raise DBConnectionException(
                "Erreur d'encodage lors de la connexion à PostgreSQL. "
                "Vérifie que la base existe et que le message d'erreur "
                "renvoyé par le serveur n'est pas encodé en dehors de l'UTF-8."
            ) from e
        except psycopg2.OperationalError as e:
            # Regroupe les erreurs opérationnelles les plus courantes :
            # base inexistante, mauvais identifiants, serveur injoignable...
            raise DBConnectionException(
                f"Impossible de se connecter à PostgreSQL "
                f"(host={db_config.get('host')}, dbname={db_config.get('dbname')}) : {e}"
            ) from e

        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table_if_not_exists(self):
        if self.conn is None:
            raise DBConnectionException(
                "Impossible de créer la table : aucune connexion active. "
                "Appelle connect() avant create_table_if_not_exists()."
            )

        query = """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(255),
            gender VARCHAR(20),
            country_code VARCHAR(10),
            company_name VARCHAR(255),
            job_title VARCHAR(255),
            departement VARCHAR(100),
            years_experience INTEGER
        );
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DBQueryException(
                f"Erreur lors de la création de la table 'employees' : {e}"
            ) from e

    def upsert_dataframe(self, df, table_name="employees"):
        if df.empty:
            print("Aucune donnée à charger.")
            return

        if self.conn is None:
            raise DBConnectionException(
                "Impossible d'upserter les données : aucune connexion active. "
                "Appelle connect() avant upsert_dataframe()."
            )

        columns = list(df.columns)
        values = [tuple(row) for row in df[columns].itertuples(index=False, name=None)]

        insert_query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'id')}
        """

        try:
            with self.conn.cursor() as cur:
                execute_values(cur, insert_query, values)
            self.conn.commit()
        except psycopg2.Error as e:
            # En cas d'échec, on annule la transaction en cours pour ne pas
            # laisser la connexion dans un état incohérent pour la suite.
            self.conn.rollback()
            raise DBQueryException(
                f"Erreur lors de l'upsert dans '{table_name}' : {e}"
            ) from e

        print(f"{len(values)} lignes upsertées dans '{table_name}'")