import os
import pytest
import pandas as pd

from util.data_transformer import DataTransformer
from util.exceptions import FileHandlingException


@pytest.fixture
def dirs(tmp_path):
    """Crée des dossiers input/output temporaires et réels."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    # output_dir n'est PAS créé ici volontairement : transform_and_save
    # doit le créer lui-même via os.makedirs(exist_ok=True)
    return str(input_dir), str(output_dir)


@pytest.fixture
def transformer(dirs):
    """DataTransformer avec un config_handler mocké (input/output réels temporaires)."""
    input_dir, output_dir = dirs

    class FakeConfigHandler:
        def get_input_dir(self):
            return input_dir

        def get_output_dir(self):
            return output_dir

    return DataTransformer(FakeConfigHandler())


def write_csv(input_dir, filename, content):
    path = os.path.join(input_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestLoadAllCsv:

    def test_no_csv_files_raises_exception(self, transformer):
        """Dossier input vide -> FileHandlingException."""
        with pytest.raises(FileHandlingException, match="Aucun fichier CSV"):
            transformer._load_all_csv()

    def test_merges_multiple_csv_files(self, transformer, dirs):
        input_dir, _ = dirs
        write_csv(input_dir, "a.csv", "id,name\n1,Alice\n2,Bob\n")
        write_csv(input_dir, "b.csv", "id,name\n3,Charlie\n")

        merged = transformer._load_all_csv()

        assert len(merged) == 3
        assert set(merged["id"]) == {1, 2, 3}

    def test_corrupted_csv_raises_exception(self, transformer, dirs):
        """Un fichier CSV malformé doit lever une FileHandlingException explicite."""
        input_dir, _ = dirs
        # Ligne avec un nombre de colonnes incohérent pour forcer un ParserError
        write_csv(input_dir, "bad.csv", 'id,name\n1,"Alice\n2,Bob\n')

        with pytest.raises(FileHandlingException, match="Impossible de lire le fichier"):
            transformer._load_all_csv()


class TestClean:

    def test_removes_duplicates_by_id(self, transformer):
        df = pd.DataFrame({
            "id": [1, 1, 2],
            "email": ["a@test.com", "a@test.com", "b@test.com"],
        })
        cleaned = transformer._clean(df)
        assert len(cleaned) == 2

    def test_strips_whitespace_on_text_columns(self, transformer):
        df = pd.DataFrame({
            "id": [1],
            "email": ["  a@test.com  "],
            "name": ["  Alice  "],
        })
        cleaned = transformer._clean(df)
        assert cleaned.loc[0, "name"] == "Alice"

    def test_normalizes_email_country_gender(self, transformer):
        df = pd.DataFrame({
            "id": [1],
            "email": ["ALICE@TEST.COM"],
            "country_code": ["ma"],
            "gender": ["female"],
        })
        cleaned = transformer._clean(df)
        assert cleaned.loc[0, "email"] == "alice@test.com"
        assert cleaned.loc[0, "country_code"] == "MA"
        assert cleaned.loc[0, "gender"] == "Female"

    def test_drops_rows_with_missing_critical_values(self, transformer):
        df = pd.DataFrame({
            "id": [1, 2],
            "email": ["a@test.com", ""],
        })
        cleaned = transformer._clean(df)
        assert len(cleaned) == 1
        assert cleaned.loc[0, "id"] == 1

    def test_fills_non_critical_missing_values_with_unknown(self, transformer):
        df = pd.DataFrame({
            "id": [1],
            "email": ["a@test.com"],
            "city": [None],
        })
        cleaned = transformer._clean(df)
        assert cleaned.loc[0, "city"] == "Unknown"

    def test_years_experience_converted_to_int_with_default_zero(self, transformer):
        df = pd.DataFrame({
            "id": [1, 2],
            "email": ["a@test.com", "b@test.com"],
            "years_experience": ["5", "not_a_number"],
        })
        cleaned = transformer._clean(df)
        assert cleaned.loc[0, "years_experience"] == 5
        assert cleaned.loc[1, "years_experience"] == 0

    def test_id_converted_to_int(self, transformer):
        df = pd.DataFrame({
            "id": ["1", "2"],
            "email": ["a@test.com", "b@test.com"],
        })
        cleaned = transformer._clean(df)
        assert cleaned["id"].dtype == int


class TestTransformAndSave:

    def test_empty_merged_dataframe_raises_exception(self, transformer, dirs, monkeypatch):
        """Si le CSV fusionné est vide (0 lignes), FileHandlingException doit être levée."""
        input_dir, _ = dirs
        write_csv(input_dir, "empty.csv", "id,email\n")  # header seul, 0 lignes

        with pytest.raises(FileHandlingException, match="rien à transformer"):
            transformer.transform_and_save()

    def test_creates_output_dir_and_saves_file(self, transformer, dirs):
        """output_dir doit être créé automatiquement s'il n'existe pas."""
        input_dir, output_dir = dirs
        write_csv(input_dir, "a.csv", "id,email\n1,a@test.com\n2,b@test.com\n")

        df_clean, output_path = transformer.transform_and_save()

        assert os.path.isdir(output_dir)
        assert os.path.isfile(output_path)
        assert len(df_clean) == 2

    def test_output_file_content_matches_dataframe(self, transformer, dirs):
        input_dir, _ = dirs
        write_csv(input_dir, "a.csv", "id,email\n1,ALICE@TEST.COM\n")

        df_clean, output_path = transformer.transform_and_save()
        reloaded = pd.read_csv(output_path)

        assert reloaded.loc[0, "email"] == "alice@test.com"

    def test_write_error_raises_filehandling_exception(self, transformer, dirs, monkeypatch):
        """Si l'écriture du CSV final échoue (ex: to_csv lève OSError), exception levée."""
        input_dir, _ = dirs
        write_csv(input_dir, "a.csv", "id,email\n1,a@test.com\n")

        def fake_to_csv(self, *args, **kwargs):
            raise OSError("disque plein")

        monkeypatch.setattr(pd.DataFrame, "to_csv", fake_to_csv)

        with pytest.raises(FileHandlingException, match="Impossible de sauvegarder"):
            transformer.transform_and_save()