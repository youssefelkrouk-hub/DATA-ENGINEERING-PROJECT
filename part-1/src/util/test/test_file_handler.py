import os
import pytest
from unittest.mock import patch

from util.file_handler import FileHandler
from util.exceptions import FileHandlingException, RegistryException


@pytest.fixture
def dirs(tmp_path):
    """Dossier input réel + chemin de registry (fichier pas forcément créé)."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    registry_file = tmp_path / "registry.txt"
    return str(input_dir), str(registry_file)


@pytest.fixture
def file_handler(dirs):
    input_dir, registry_file = dirs

    with patch("util.file_handler.ConfigHandler") as MockConfigHandler:
        mock_config = MockConfigHandler.return_value
        mock_config.get_input_dir.return_value = input_dir
        mock_config.get_registry_file.return_value = registry_file

        handler = FileHandler()
        yield handler


def write_file(directory, filename, content=""):
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestListFiles:

    def test_missing_directory_raises_exception(self, file_handler):
        file_handler.directory = "/chemin/qui/nexiste/pas/123456"
        with pytest.raises(FileHandlingException, match="introuvable"):
            file_handler.list_files()

    def test_returns_only_csv_files(self, file_handler, dirs):
        input_dir, _ = dirs
        write_file(input_dir, "a.csv")
        write_file(input_dir, "b.csv")
        write_file(input_dir, "notes.txt")

        files = file_handler.list_files()

        assert sorted(files) == ["a.csv", "b.csv"]

    def test_ignores_subdirectories_even_if_named_csv(self, file_handler, dirs):
        input_dir, _ = dirs
        os.mkdir(os.path.join(input_dir, "fake.csv"))
        write_file(input_dir, "real.csv")

        files = file_handler.list_files()

        assert files == ["real.csv"]

    def test_empty_directory_returns_empty_list(self, file_handler):
        assert file_handler.list_files() == []


class TestLoadRegistry:

    def test_creates_registry_file_if_missing(self, file_handler, dirs):
        _, registry_file = dirs
        assert not os.path.exists(registry_file)

        result = file_handler.load_registry()

        assert os.path.exists(registry_file)
        assert result == set()

    def test_loads_existing_filenames(self, file_handler, dirs):
        _, registry_file = dirs
        with open(registry_file, "w") as f:
            f.write("a.csv\t2026-01-01 10:00:00\n")
            f.write("b.csv\t2026-01-02 11:00:00\n")

        result = file_handler.load_registry()

        assert result == {"a.csv", "b.csv"}

    def test_ignores_blank_lines(self, file_handler, dirs):
        _, registry_file = dirs
        with open(registry_file, "w") as f:
            f.write("a.csv\t2026-01-01 10:00:00\n")
            f.write("\n")
            f.write("   \n")
            f.write("b.csv\t2026-01-02 11:00:00\n")

        result = file_handler.load_registry()

        assert result == {"a.csv", "b.csv"}

    def test_registry_creation_error_raises_registry_exception(self, file_handler, monkeypatch):
        """Si le registry n'existe pas et que sa création échoue (ex: dossier invalide)."""
        file_handler.registry_file = "/chemin/qui/nexiste/pas/123456/registry.txt"

        with pytest.raises(RegistryException, match="Impossible de créer"):
            file_handler.load_registry()

    def test_read_error_raises_registry_exception(self, file_handler, dirs, monkeypatch):
        _, registry_file = dirs
        with open(registry_file, "w") as f:
            f.write("a.csv\t2026-01-01 10:00:00\n")

        def fake_open(*args, **kwargs):
            raise OSError("erreur disque")

        monkeypatch.setattr("builtins.open", fake_open)

        with pytest.raises(RegistryException, match="Impossible de lire"):
            file_handler.load_registry()


class TestUpdateRegistry:

    def test_no_new_files_does_nothing(self, file_handler, dirs):
        _, registry_file = dirs
        file_handler.update_registry([])
        assert not os.path.exists(registry_file)

    def test_appends_new_files_with_timestamp(self, file_handler, dirs):
        _, registry_file = dirs
        file_handler.update_registry(["a.csv", "b.csv"])

        with open(registry_file, "r") as f:
            lines = f.read().splitlines()

        assert len(lines) == 2
        assert lines[0].startswith("a.csv\t")
        assert lines[1].startswith("b.csv\t")

    def test_appends_without_overwriting_existing_content(self, file_handler, dirs):
        _, registry_file = dirs
        with open(registry_file, "w") as f:
            f.write("old.csv\t2026-01-01 10:00:00\n")

        file_handler.update_registry(["new.csv"])

        with open(registry_file, "r") as f:
            lines = f.read().splitlines()

        assert len(lines) == 2
        assert lines[0].startswith("old.csv")
        assert lines[1].startswith("new.csv")

    def test_write_error_raises_registry_exception(self, file_handler):
        file_handler.registry_file = "/chemin/qui/nexiste/pas/123456/registry.txt"

        with pytest.raises(RegistryException, match="Impossible de mettre à jour"):
            file_handler.update_registry(["a.csv"])


class TestTrackNewFiles:

    def test_returns_only_unprocessed_files_and_updates_registry(self, file_handler, dirs):
        input_dir, registry_file = dirs
        write_file(input_dir, "old.csv")
        write_file(input_dir, "new.csv")
        with open(registry_file, "w") as f:
            f.write("old.csv\t2026-01-01 10:00:00\n")

        new_files = file_handler.track_new_files()

        assert new_files == ["new.csv"]
        with open(registry_file, "r") as f:
            content = f.read()
        assert "new.csv" in content

    def test_no_files_at_all_returns_empty_list(self, file_handler):
        new_files = file_handler.track_new_files()
        assert new_files == [] 