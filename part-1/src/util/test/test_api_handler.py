import pytest
from unittest.mock import patch, MagicMock
import requests

from util.api_handler import ApiHandler
from util.exceptions import ApiRequestException


@pytest.fixture
def api_handler(tmp_path):
    """
    Crée une instance d'ApiHandler avec un ConfigHandler mocké,
    pointant vers un dossier temporaire pour l'écriture des fichiers.
    """
    with patch("util.api_handler.ConfigHandler") as MockConfigHandler:
        mock_config = MockConfigHandler.return_value
        mock_config.get_api_url.return_value = "http://fake-api.test/jobs"
        mock_config.get_input_dir.return_value = str(tmp_path)

        handler = ApiHandler()
        yield handler


class TestGetDataToCsv:

    @patch("util.api_handler.requests.get")
    def test_success_creates_csv_file(self, mock_get, api_handler, tmp_path):
        """Cas nominal : la réponse est 200, le fichier CSV doit être créé avec le bon contenu."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "id,title\n1,Data Engineer\n"
        mock_get.return_value = mock_response

        api_handler.get_data_to_csv()

        files = list(tmp_path.glob("JOBS_v1_*.csv"))
        assert len(files) == 1
        assert files[0].read_text(encoding="utf-8") == "id,title\n1,Data Engineer\n"

    @patch("util.api_handler.requests.get")
    def test_non_200_status_raises_exception(self, mock_get, api_handler):
        """Si le status code n'est pas 200, une ApiRequestException doit être levée."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ApiRequestException, match="404"):
            api_handler.get_data_to_csv()

    @patch("util.api_handler.requests.get")
    def test_network_error_raises_exception(self, mock_get, api_handler):
        """Si requests.get lève une exception réseau, elle doit être encapsulée dans ApiRequestException."""
        mock_get.side_effect = requests.exceptions.ConnectionError("connexion refusée")

        with pytest.raises(ApiRequestException, match="Erreur réseau"):
            api_handler.get_data_to_csv()

    @patch("util.api_handler.requests.get")
    def test_timeout_raises_exception(self, mock_get, api_handler):
        """Un timeout doit aussi être encapsulé dans ApiRequestException."""
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with pytest.raises(ApiRequestException, match="Erreur réseau"):
            api_handler.get_data_to_csv()

    @patch("util.api_handler.requests.get")
    def test_file_write_error_raises_exception(self, mock_get, api_handler):
        """Si l'écriture du fichier échoue (ex: dossier invalide), ApiRequestException doit être levée."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "id,title\n1,Data Engineer\n"
        mock_get.return_value = mock_response

        # On force une erreur d'écriture en changeant le input_dir vers un chemin invalide
        api_handler.input_dir = "/chemin/qui/nexiste/pas/123456"

        with pytest.raises(ApiRequestException, match="Impossible d'écrire"):
            api_handler.get_data_to_csv()

    @patch("util.api_handler.requests.get")
    def test_correct_url_is_called(self, mock_get, api_handler):
        """Vérifie que l'URL de l'API configurée est bien celle utilisée par requests.get."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "id,title\n1,Data Engineer\n"
        mock_get.return_value = mock_response

        api_handler.get_data_to_csv()

        mock_get.assert_called_once_with("http://fake-api.test/jobs", timeout=10)