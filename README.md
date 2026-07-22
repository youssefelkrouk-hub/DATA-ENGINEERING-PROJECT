# Data-Engineering-101 -> PART 1 DOC

### 1. Description
This repo is a hands-on guide to learning modern data engineering by building a small end-to-end ETL pipeline: fetching data from an API, transforming it, and loading it into a relational database (PostgreSQL).

### 2. Getting Started

#### 2.1 Prerequisites
1. Install Python (developed with Python 3.13.x)
2. Create a virtual environment
   - Install: `pip install virtualenv`
   - Create a dedicated folder for your virtual env (kept separate from this project)
   - Create the folder: `mkdir virtual-env`
   - Create the virtual env inside it: `python -m venv virtual-env\space-env`
   - Activate it from the root folder (PowerShell): `virtual-env\space-env\Scripts\Activate.ps1`
   - If activation is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
   - (Alternative for cmd.exe): `virtual-env\space-env\Scripts\activate.bat`
3. Install dependencies from `requirements.txt` (run from your activated virtual env):
   - `pip install -r requirements.txt`
4. Save `requirements.txt` for reproducibility (run from `part-1`):
   - `pip freeze > requirements.txt`
5. Set up `config/config.ini` based on `config.ini.template`, filling in your own API URL, paths, and database credentials.

#### 2.2 Run It
After setting up your environment and config, run the pipeline entry points from `part-1/src`:

```bash
python main_fetch_save.py    # fetches data from the API and saves timestamped CSVs to input/
python main_transform.py     # merges and cleans new CSVs, saves result to output/
python main_load_db.py       # loads the cleaned data into PostgreSQL
```

### 3. Src Walkthrough

#### 3.1 Overview
- `input/` and `output/` represent our source and target file systems for the raw and curated layers.
- `src/` contains the pipeline entry points (`main_fetch_save.py`, `main_transform.py`, `main_load_db.py`) along with the `config/` and `util/` packages.
- `config/` holds configuration files (`config.ini`, `registry.txt`).
- `util/` holds all reusable logic: API access, file handling, transformation, database access, scheduling, and shared exceptions.

#### 3.2 Util Package

##### 3.2.1 API Handler (`api_handler.py`)
Calls the configured API (Mockaroo) and saves the raw response as a timestamped CSV in `input/`. Logs the elapsed time of the API call for basic performance visibility. Raises `ApiRequestException` on network errors, non-200 responses, or file write failures.

##### 3.2.2 Config Handler (`config_handler.py`)
Centralizes all configuration reads from `config.ini` via `configparser`. Exposes typed getters (`get_api_url`, `get_input_dir`, `get_output_dir`, `get_registry_file`, `get_db_config`) and raises `InvalidValueException` on missing or empty values.

##### 3.2.3 Data Transformer (`data_transformer.py`)
Merges all CSV files found in `input/` into a single DataFrame, applies cleaning rules (deduplication, whitespace trimming, normalization of email/country/gender fields, missing-value handling, type coercion), and saves the cleaned result as a timestamped CSV in `output/`. Raises `FileHandlingException` on read, merge, or write errors.

##### 3.2.4 DB Handler (`db_handler.py`)
Manages the PostgreSQL connection lifecycle (`connect`, `close`), creates the `employees` table if it doesn't exist, and upserts a cleaned DataFrame into it using `ON CONFLICT ... DO UPDATE`. Raises `DBConnectionException` or `DBQueryException` as appropriate.

##### 3.2.5 File Handler (`file_handler.py`)
Tracks which files in `input/` have already been processed, using `registry.txt` as a persistent log. Supports listing new `.csv` files, loading/creating the registry, and appending newly seen filenames with a timestamp.

##### 3.2.6 Scheduler (`scheduler.py`)
Orchestrates recurring pipeline runs using the `schedule` library — periodically calling `ApiHandler.get_data_to_csv` and `FileHandler.track_new_files`. Wraps each job in a `_safe_run` helper so a single failing job doesn't crash the whole scheduling loop. (For production-grade orchestration, a tool like Airflow would replace this.)

##### 3.2.7 Exceptions (`exceptions.py`)
Defines a shared exception hierarchy (`ProjectBaseException` and subclasses: `ApiRequestException`, `InvalidValueException`, `FileHandlingException`, `RegistryException`, `DBConnectionException`, `DBQueryException`) used consistently across all modules for predictable error handling.

### 3.3 Config Package

##### 3.3.1 Registry (`registry.txt`)
Contains the list of already-processed input files (filename + timestamp), used to avoid reprocessing and to keep an audit trail.

##### 3.3.2 config.ini
Holds all configuration, currently structured as:
- `[API]` — API URL (`url`)
- `[Paths]` — `input_dir`, `output_dir`, `registry_file`
- `[Database]` — PostgreSQL connection details (`host`, `port`, `dbname`, `user`, `password`)

Use the same structure as `config.ini.template`, filling in your own values. **Never commit real credentials** — `config.ini` should be gitignored.

### 3.4 Pipeline Layers
- **Raw layer**: fetch data from the API and store it as timestamped CSVs in `input/`.
- **Curated layer**: merge and clean new files from `input/` into a single cleaned CSV in `output/`.
- **Load layer**: upsert the curated data into PostgreSQL.

### 4. Testing

#### 4.1 Unit Tests
Testing is done with `pytest`, using `unittest.mock` for isolation (mocking `requests`, `psycopg2`, `ConfigHandler`, `schedule`, etc.) and `tmp_path` fixtures for real, disposable file I/O where relevant.

Test files live under `util/test/` and cover:
- **`test_api_handler.py`** — successful fetch, HTTP errors, network errors, timeouts, file write errors, correct URL usage.
- **`test_config_handler.py`** — successful reads, missing sections/options, empty values, value stripping.
- **`test_data_transform.py`** — CSV loading and merging, cleaning rules (dedup, normalization, missing values, type coercion), empty-input handling, save errors.
- **`test_db_handler.py`** — connection success/failure, table creation, upsert logic, rollback on query errors.
- **`test_file_handler.py`** — listing CSVs, registry creation/loading/updating, new-file tracking.
- **`test_scheduler.py`** — safe job execution, error isolation, job scheduling and loop resilience.

Run the full suite from the project root:
```bash
pytest -v
```

Run a specific file:
```bash
pytest util/test/test_api_handler.py -v
```

### 5. Development Workflow

#### 5.1 .gitignore
For files that are already tracked and should be ignored going forward, untrack them first, then commit:
```bash
git rm -r --cached <file-or-folder-path>   # use -r for folders
```

#### 5.2 Branching & Pull Requests
- Work on feature branches (e.g. `feature/db-upsert`, `fix/config-encoding`) rather than committing directly to `main`.
- Keep branches focused on a single change, and merge `main` into your branch regularly to avoid large conflicts:
```bash
  git fetch origin
  git merge origin/main
```
- Open a Pull Request with a clear title and description before merging into `main`.
- Prefer **Squash and merge** for a clean, linear history on `main`.
- Delete the branch after merging.

### 6. Clean-Up

#### 6.1 Delete Generated Files
Make sure you're in the root directory:
```bash
rm ./part-1/input/*.csv
rm ./part-1/output/*.csv
```

### 7. Roadmap / TODO
- [ ] Ensure code complies with Python best practices (naming, typing where useful)
- [ ] Replace the custom `Scheduler` with a proper orchestrator (e.g. Airflow) for production use

### Pipeline Overview

```
[Scheduler]
     │
     ▼
Every N seconds/minutes
     │
     ▼
[ApiHandler] ──► calls Mockaroo API ──► saves timestamped CSV in input/
     │
     ▼
[FileHandler] ──► scans input/ for .csv files ──► compares with registry.txt ──► logs new files
     │
     ▼
[DataTransformer] ──► merges & cleans new CSVs ──► saves curated CSV in output/
     │
     ▼
[DBHandler] ──► upserts curated data into PostgreSQL
```