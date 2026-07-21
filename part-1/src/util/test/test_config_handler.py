import configparser
import pytest

from util.config_handler import ConfigHandler
from util.exceptions import InvalidValueException


VALID_CONFIG = """
[API]
url=https://my.api.mockaroo.com/employees.json?key=abc123

[Paths]
input_dir=../input
output_dir=../output
registry_file=config/registry.txt

[Database]
host=localhost
port=5432
dbname=jobshandler_db
user=postgres
password=secret123
"""


@pytest.fixture
def make_config_handler(monkeypatch):
    """
    Factory de fixture : construit un ConfigHandler dont le ConfigParser
    interne est alimenté par une chaîne de config personnalisée, sans
    toucher au vrai fichier config.ini sur le disque.
    """
    def _make(content=VALID_CONFIG, file_found=True):
        def fake_read(self, filenames, encoding=None):
            if not file_found:
                return []  # simule un fichier introuvable
            self.read_string(content)
            return [filenames]  # simule un retour "trouvé" de configparser

        monkeypatch.setattr(configparser.ConfigParser, "read", fake_read)
        return ConfigHandler()

    return _make


class TestConfigHandlerInit:

    def test_missing_file_raises_filenotfound(self, make_config_handler):
        """Si le fichier config.ini est introuvable, une FileNotFoundError doit être levée."""
        with pytest.raises(FileNotFoundError, match="Config introuvable"):
            make_config_handler(file_found=False)


class TestGetters:

    def test_get_api_url_success(self, make_config_handler):
        handler = make_config_handler()
        assert handler.get_api_url() == "https://my.api.mockaroo.com/employees.json?key=abc123"

    def test_get_input_dir_success(self, make_config_handler):
        handler = make_config_handler()
        assert handler.get_input_dir() == "../input"

    def test_get_output_dir_success(self, make_config_handler):
        handler = make_config_handler()
        assert handler.get_output_dir() == "../output"

    def test_get_registry_file_success(self, make_config_handler):
        handler = make_config_handler()
        assert handler.get_registry_file() == "config/registry.txt"

    def test_get_db_config_success(self, make_config_handler):
        handler = make_config_handler()
        db_config = handler.get_db_config()

        assert db_config == {
            "host": "localhost",
            "port": "5432",
            "dbname": "jobshandler_db",
            "user": "postgres",
            "password": "secret123",
        }

    def test_value_is_stripped(self, make_config_handler):
        """Les espaces superflus autour de la valeur doivent être retirés."""
        content = VALID_CONFIG.replace(
            "url=https://my.api.mockaroo.com/employees.json?key=abc123",
            "url=   https://my.api.mockaroo.com/employees.json?key=abc123   ",
        )
        handler = make_config_handler(content=content)
        assert handler.get_api_url() == "https://my.api.mockaroo.com/employees.json?key=abc123"


class TestMissingOrEmptyValues:

    def test_missing_section_raises_invalid_value_exception(self, make_config_handler):
        """Si une section entière est absente, InvalidValueException doit être levée."""
        content = """
[Paths]
input_dir=../input
output_dir=../output
registry_file=config/registry.txt

[Database]
host=localhost
port=5432
dbname=jobshandler_db
user=postgres
password=secret123
"""
        handler = make_config_handler(content=content)
        with pytest.raises(InvalidValueException, match=r"\[API\] url"):
            handler.get_api_url()

    def test_missing_option_raises_invalid_value_exception(self, make_config_handler):
        """Si une option précise est absente dans une section existante, exception levée."""
        content = """
[API]
url=https://my.api.mockaroo.com/employees.json?key=abc123

[Paths]
output_dir=../output
registry_file=config/registry.txt

[Database]
host=localhost
port=5432
dbname=jobshandler_db
user=postgres
password=secret123
"""
        handler = make_config_handler(content=content)
        with pytest.raises(InvalidValueException, match=r"\[Paths\] input_dir"):
            handler.get_input_dir()

    def test_empty_value_raises_invalid_value_exception(self, make_config_handler):
        """Si une valeur existe mais est vide (ou juste des espaces), exception levée."""
        content = VALID_CONFIG.replace(
            "password=secret123", "password=   "
        )
        handler = make_config_handler(content=content)
        with pytest.raises(InvalidValueException, match="vide"):
            handler.get_db_config()