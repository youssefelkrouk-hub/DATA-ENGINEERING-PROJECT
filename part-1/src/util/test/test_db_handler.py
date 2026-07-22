import pytest
from unittest.mock import patch, MagicMock
import psycopg2
import pandas as pd

from util.db_handler import DBHandler
from util.exceptions import DBConnectionException, DBQueryException


@pytest.fixture
def fake_db_config():
    return {
        "host": "localhost",
        "port": "5432",
        "dbname": "jobshandler_db",
        "user": "postgres",
        "password": "secret123",
    }


@pytest.fixture
def handler(fake_db_config):
    class FakeConfigHandler:
        def get_db_config(self):
            return dict(fake_db_config)  # copie pour éviter les effets de bord

    return DBHandler(FakeConfigHandler())


def make_mock_conn():
    """
    Crée une connexion mockée dont conn.cursor() se comporte comme un
    context manager (support du `with self.conn.cursor() as cur:`).
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False
    return mock_conn, mock_cursor


class TestConnect:

    @patch("util.db_handler.psycopg2.connect")
    def test_connect_success(self, mock_connect, handler):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = handler.connect()

        assert result is mock_conn
        assert handler.conn is mock_conn

    @patch("util.db_handler.psycopg2.connect")
    def test_connect_forces_utf8_encoding(self, mock_connect, handler):
        mock_connect.return_value = MagicMock()

        handler.connect()

        _, kwargs = mock_connect.call_args
        assert kwargs["client_encoding"] == "utf8"

    @patch("util.db_handler.psycopg2.connect")
    def test_operational_error_raises_db_connection_exception(self, mock_connect, handler):
        mock_connect.side_effect = psycopg2.OperationalError("connexion refusée")

        with pytest.raises(DBConnectionException, match="Impossible de se connecter"):
            handler.connect()

    @patch("util.db_handler.psycopg2.connect")
    def test_unicode_decode_error_raises_db_connection_exception(self, mock_connect, handler, capsys):
        mock_connect.side_effect = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte")

        with pytest.raises(DBConnectionException, match="encodage"):
            handler.connect()

        # Vérifie que le détail des paramètres est bien loggé pour debug
        captured = capsys.readouterr()
        assert "Erreur d'encodage" in captured.out


class TestClose:

    def test_close_calls_conn_close_when_connected(self, handler):
        mock_conn = MagicMock()
        handler.conn = mock_conn

        handler.close()

        mock_conn.close.assert_called_once()

    def test_close_does_nothing_when_not_connected(self, handler):
        handler.conn = None
        handler.close()  # ne doit pas lever d'exception


class TestCreateTableIfNotExists:

    def test_raises_if_no_connection(self, handler):
        handler.conn = None
        with pytest.raises(DBConnectionException, match="aucune connexion active"):
            handler.create_table_if_not_exists()

    def test_creates_table_and_commits(self, handler):
        mock_conn, mock_cursor = make_mock_conn()
        handler.conn = mock_conn

        handler.create_table_if_not_exists()

        mock_cursor.execute.assert_called_once()
        assert "CREATE TABLE IF NOT EXISTS employees" in mock_cursor.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()

    def test_query_error_rolls_back_and_raises(self, handler):
        mock_conn, mock_cursor = make_mock_conn()
        mock_cursor.execute.side_effect = psycopg2.Error("erreur SQL")
        handler.conn = mock_conn

        with pytest.raises(DBQueryException, match="Erreur lors de la création"):
            handler.create_table_if_not_exists()

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()


class TestUpsertDataframe:

    def test_empty_dataframe_does_nothing(self, handler, capsys):
        handler.conn = MagicMock()
        df = pd.DataFrame()

        handler.upsert_dataframe(df)

        handler.conn.cursor.assert_not_called()
        captured = capsys.readouterr()
        assert "Aucune donnée à charger" in captured.out

    def test_raises_if_no_connection(self, handler):
        handler.conn = None
        df = pd.DataFrame({"id": [1], "email": ["a@test.com"]})

        with pytest.raises(DBConnectionException, match="aucune connexion active"):
            handler.upsert_dataframe(df)

    @patch("util.db_handler.execute_values")
    def test_upsert_success_calls_execute_values_and_commits(self, mock_execute_values, handler):
        mock_conn, mock_cursor = make_mock_conn()
        handler.conn = mock_conn
        df = pd.DataFrame({
            "id": [1, 2],
            "email": ["a@test.com", "b@test.com"],
        })

        handler.upsert_dataframe(df, table_name="employees")

        mock_execute_values.assert_called_once()
        args, _ = mock_execute_values.call_args
        cur_arg, query_arg, values_arg = args
        assert cur_arg is mock_cursor
        assert "INSERT INTO employees" in query_arg
        assert "ON CONFLICT (id) DO UPDATE SET" in query_arg
        assert values_arg == [(1, "a@test.com"), (2, "b@test.com")]
        mock_conn.commit.assert_called_once()

    @patch("util.db_handler.execute_values")
    def test_upsert_query_error_rolls_back_and_raises(self, mock_execute_values, handler):
        mock_conn, mock_cursor = make_mock_conn()
        mock_execute_values.side_effect = psycopg2.Error("erreur upsert")
        handler.conn = mock_conn
        df = pd.DataFrame({"id": [1], "email": ["a@test.com"]})

        with pytest.raises(DBQueryException, match="Erreur lors de l'upsert"):
            handler.upsert_dataframe(df)

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    @patch("util.db_handler.execute_values")
    def test_upsert_excludes_id_from_update_clause(self, mock_execute_values, handler):
        """La clause ON CONFLICT ne doit pas essayer de mettre à jour 'id' lui-même."""
        mock_conn, mock_cursor = make_mock_conn()
        handler.conn = mock_conn
        df = pd.DataFrame({"id": [1], "email": ["a@test.com"], "gender": ["Female"]})

        handler.upsert_dataframe(df)

        _, query_arg, _ = mock_execute_values.call_args[0]
        assert "id = EXCLUDED.id" not in query_arg
        assert "email = EXCLUDED.email" in query_arg
        assert "gender = EXCLUDED.gender" in query_arg