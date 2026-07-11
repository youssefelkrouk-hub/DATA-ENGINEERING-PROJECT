# Data-Engineering-101 -> PART 1 DOC

### 1. Description
This repo should be your guide in learning by doing modern data engineering

### 2. Getting started
#### 2.1 Prerequisites
1. Install python (I'm using Python 3.13.6)
2. Create virtual env 
    - > Install : pip install virtualenv
    - > Create dedicated folder for your virtual env (separated from this project)
    - > Create new folder : mkdir virtual-env
    - > Create Virtual Env inside virtual-env : python -m venv virtual-env\space-env
    - > Activate Virtual Env from root folder (PowerShell) : virtual-env\space-env\Scripts\Activate.ps1
    - > If activation is blocked, run once : Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    - > (Alternative for cmd.exe) : virtual-env\space-env\Scripts\activate.bat
3. Install requirements.txt packages (run from your virtual env and to install the packages that i use in my code)
    - > pip install -r requirements.txt 
4. Save requirements.txt for results reproducibility (run from part-1)
    - > pip freeze > requirements.txt
5. Install PostgreSQL locally (used as the target database for the load layer)
    - > Download from https://www.postgresql.org/download/
    - > During setup, note down the port (default 5432) and the password you set for the `postgres` user
    - > Create a dedicated database for this project (e.g. `jobshandler_db`), either via pgAdmin or:
      ```sql
      CREATE DATABASE jobshandler_db;
      ```

#### 2.2 Run IT
After setting up your ENV, run each pipeline stage individually from the `src/` folder:

```bash
cd src

# Step 1 — Extract: fetch data from API and save raw CSV
python main_fetch_save.py

# Step 2 — Transform: clean and merge raw files into a curated CSV
python main_transform.py

# Step 3 — Load: insert curated CSV into PostgreSQL
python main_load_db.py

# Run the full pipeline automatically on a schedule
python scheduler.py
```

### 3. Src Walkthrough
#### 3.1 Overview
We have input and output folders representing our source and target systems.
We have a `src` folder where we have our pipeline entry points along with `config` and `util` folders.

The pipeline follows the **ETL pattern** (Extract → Transform → Load), split across dedicated entry points:

| File | Role | ETL Stage |
|---|---|---|
| `main_fetch_save.py` | Calls the API, saves timestamped raw CSV to `input/` | **Extract** |
| `main_transform.py` | Scans `input/`, merges new files, cleans data, saves to `output/` | **Transform** |
| `main_load_db.py` | Picks latest CSV from `output/`, upserts into PostgreSQL | **Load** |
| `scheduler.py` | Orchestrates the full pipeline on a time-based schedule | **Orchestrator** |

1. `config` package will have all our configuration files for part 1
2. `util` package will have all we need to deal with files, schedulers, etc.

#### 3.2 Util package
##### 3.2.1 File Handler
This will help us with this workflow : 3.3
1. list all files in input folder each time our scheduler is triggered
2. check registry text file in config folder for a cross-check
3. the new files only will be transfered to output folder
4. the registry will get updated with the new files names

##### 3.2.2 API Handler
This basically for calling the API and getting data as a pandas dataframe

##### 3.2.3 Config Handler
To simplify and centralize configurations, including folder paths, API names, database credentials, etc.

##### 3.2.4 Scheduler
This for orchestrating the pipelines and control when they will be triggered (we're using it in the early parts, but normally we should use Airflow for example for advanced use cases)

##### 3.2.5 Exceptions
We added a dedicated `exceptions.py` file to define custom exception classes for this project (e.g. `ApiRequestException`, `InvalidValueException`).

We use custom exceptions instead of relying only on generic Python exceptions for a few reasons:
1. **Clarity**: raising `InvalidValueException("Missing config value: ...")` tells us immediately that the problem comes from our own validation logic, not from a low-level library.
2. **Precise error handling**: calling code (and later, our unit tests) can catch specific exception types (e.g. `except InvalidValueException`) instead of catching broad, generic exceptions that might silently hide unrelated bugs.
3. **Testability**: Pytest can assert that a specific custom exception is raised in a given scenario (`pytest.raises(InvalidValueException)`), which makes our test cases more explicit and reliable.
4. **Consistency across the codebase**: every handler (Config, API, File) can raise the same well-known exception types, making error handling predictable across the whole pipeline.

##### 3.2.6 DB Handler
`db_handler.py` is responsible for everything related to loading data into PostgreSQL:
1. **Connect**: opens a connection to PostgreSQL using the credentials returned by `ConfigHandler.get_db_config()`. The client encoding is explicitly forced to `utf8` to avoid encoding mismatches between Python, the OS locale, and the PostgreSQL server.
2. **Create table**: `create_table_if_not_exists()` ensures the target table (`employees`) exists before any data is inserted, so the pipeline can run on a fresh database without manual setup.
3. **Upsert**: `upsert_dataframe()` takes a pandas DataFrame (the cleaned/curated data) and inserts it into PostgreSQL using `INSERT ... ON CONFLICT (id) DO UPDATE`, so re-running the load layer on the same data updates existing rows instead of creating duplicates.
4. **Close**: closes the connection cleanly at the end of the pipeline.

#### 3.3 Config package
##### 3.3.1 Registry
It contains list of processed files to avoid system overload and keep track of when we processed each file

##### 3.3.2 config.ini
It contains list of all our configurations, we're currently using : 
[API] section that contains : API url (url)
[Paths] section that contains : input and registry file name (raw_dir, registry_file)
[Database] section that contains : PostgreSQL connection info (host, port, dbname, user, password)
Please use the same format in the config.ini.example with your own values

##### 3.3.3 Database configuration
The `[Database]` section in `config.ini` holds everything `psycopg2` needs to connect:

```ini
[Database]
host=localhost
port=5432
dbname=jobshandler_db
user=postgres
password=your_password_here
```

⚠️ `config.ini` is excluded from version control via `.gitignore` since it contains a real password. Use `config.ini.example` as a template when setting up the project locally, and never commit real credentials.

#### 3.4 Pipelines package
This is to design how we want our pipelines to act, depending on the layer
##### 3.4.1 raw layer
For this layer, we should get data and store it in raw folder in csv formats.
##### 3.4.2 curated layer
For this layer, we should check new files and combine them in one file, this just a simple use case for part-1, 
more transformations will be introduced as we move forward.
##### 3.4.3 load layer
This layer is responsible for loading the curated/cleaned CSV into PostgreSQL, and is orchestrated by `main_load_db.py`:
1. Picks the most recently modified CSV file from the `output/` folder (the result of the curated layer)
2. Loads it into a pandas DataFrame
3. Connects to PostgreSQL via `DBHandler`
4. Creates the `employees` table if it doesn't already exist
5. Upserts the DataFrame into the table (insert new rows, update existing ones based on `id`)
6. Closes the connection

### 4. Test Walkthrough
#### 4.1 Unit Tests
For unit testing, we have used Pytest package and it's very simple.
The test cases are designed to verify the behavior of these classes under various conditions, including successful and failed API requests, and file handling operations such as saving data to CSV files.

We have used Fixture to create an instance of ApiHandler for testing.
And Mock to mock behaviour of functions and objects (return, effects, etc.)

Dependencies:
    - util.exceptions.RequestException: Custom exception class for API request failures
    - util.exceptions.InvalidValueException: Custom exception class for invalid input values
Test Cases:
    - TestApiHandler:
    - TestFileHandler:

### 5. Development Ways
#### 5.1 gitignore
1. to add files that are already tracked, execute this command first then commit your changes
- > git rm -r --cached <file-or-folder-path> (use -r for folders)

### 6. Clean-Up
#### 6.1 Delete files
Make sure you're in the root directory
> rm ./part-1/data/raw/*.csv
> rm ./part-1/data/curated/*.csv

#### 6.2 Reset the database
If you need to start fresh, either drop and recreate the database:
```sql
DROP DATABASE jobshandler_db;
CREATE DATABASE jobshandler_db;
```
or just clear the table while keeping the schema:
```sql
TRUNCATE TABLE employees;
```

### 7. Database queries
`src/main.sql` contains a collection of ready-to-use SQL queries for the `employees` table: exploration, filtering, aggregations (count by country/department, average experience by job title), sorting, and duplicate checks. Open it in pgAdmin (connected to `jobshandler_db`) to run them.

### 8. Changelog

#### [Refactor] — ETL Pipeline Restructure

Replaced legacy entry point files with a clean, single-responsibility ETL structure:

**Removed**
- `load_main.py` — load logic moved to `main_load_db.py`
- `main.py` — replaced by dedicated stage entry points
- `main1.py` — deprecated experimental entry point
- `util/main1.py` — deprecated utility script

**Added**
- `main_fetch_save.py` — **Extract**: calls the API, saves timestamped raw CSV to `input/`
- `main_transform.py` — **Transform**: merges new files, cleans data, saves curated CSV to `output/`
- `main_load_db.py` — **Load**: reads latest curated CSV, upserts into PostgreSQL
- `scheduler.py` — **Orchestrator**: triggers the full pipeline on a time-based schedule

Each file now has a single, clearly named responsibility aligned with the ETL pattern. See section 3.1 for the full entry point reference table.

### 9. TODO
- Ensure that code complies with Python best practices
- Arguments are following the Pythonic way

---

```
[Scheduler]
        │
        ▼
  Every 1 minutes
        │
        ▼
  [ApiHandler] ──► calls Mockaroo API ──► saves timestamped CSV in input/
        │
        ▼
  [FileHandler] ──► scans input/ for .csv files
        │
        ▼
  compares with registry.txt ──► logs new files
        │
        ▼
  [Transformer] ──► merges & cleans new files ──► saves cleaned CSV in output/
        │
        ▼
  [DBHandler] ──► connects to PostgreSQL ──► creates table if needed
        │
        ▼
  upserts cleaned data into `employees` table (INSERT ... ON CONFLICT DO UPDATE)
```