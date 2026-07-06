import psycopg2
from psycopg2.extras import execute_values


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
            raise e

        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()

    def create_table_if_not_exists(self):
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
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()

    def upsert_dataframe(self, df, table_name="employees"):
        if df.empty:
            print("Aucune donnée à charger.")
            return

        columns = list(df.columns)
        values = [tuple(row) for row in df[columns].itertuples(index=False, name=None)]

        insert_query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'id')}
        """

        with self.conn.cursor() as cur:
            execute_values(cur, insert_query, values)
        self.conn.commit()
        print(f"{len(values)} lignes upsertées dans '{table_name}'")