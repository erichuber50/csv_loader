# README.md

## CSV Loader

[![codecov](https://codecov.io/gh/erichuber50/csv_loader/branch/main/graph/badge.svg)](https://codecov.io/gh/erichuber50/csv_loader)

This project provides a command-line tool for dynamically creating a PostgreSQL database schema from a CSV schema definition (`INFORMATION_SCHEMA.csv`), loading data from CSV files, and running analysis queries.

---

## Features

- **Dynamic Table Creation:**  
  Reads a schema definition from `INFORMATION_SCHEMA.csv` and creates tables automatically.

- **CSV Data Loading:**  
  Loads all CSV files in a specified directory into their corresponding tables, with schema validation.

- **Analysis Queries:**  
  Includes built-in queries for overdrawn checking accounts, overpaid loans, and total assets.

- **Schema Validation:**  
  Validates CSV columns against the schema, warns about mismatches, and skips invalid files.

- **Data Integrity Verification:**  
  Verifies that all records in a given file have been successfully inserted into the database.

- **Schema Drift Handling:**  
  Accounts for changes in the files over time, including column additions, removals, and column order changes.

---

## Requirements

- Python 3.8+
- PostgreSQL database

---

## Getting Started

### 1. Clone the Repository

```
git clone https://github.com/erichuber50/csv_loader.git
cd csv_loader
```

### 2. Set Up PostgreSQL

1. [Download and install PostgreSQL](https://www.postgresql.org/download/).

2. Open a terminal or command prompt and launch the PostgreSQL interactive terminal (`psql`).  
   If you installed PostgreSQL locally, you can usually start `psql` with:
   ```
   psql -U postgres
   ```
   - `-U postgres` connects as the default `postgres` superuser.
   - You may need to enter your password.

3. Create a new database and user (run in the psql prompt connected as postgres):
   ```
   -- Create database and user
   CREATE DATABASE your_db_name;
   CREATE USER your_user WITH PASSWORD 'your_password';

   -- Grant database privileges
   GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_user;

   -- Connect to the new database
   \c your_db_name

   -- Make the user the owner of the database schema
   ALTER DATABASE your_db_name OWNER TO your_user;
   ALTER SCHEMA public OWNER TO your_user;
   ```
4. Exit with:
   ```
   \q
   ```

5. **Set the `DATABASE_URL` environment variable** to use the new database and user credentials:

   **Windows (PowerShell):**
   ```
   $env:DATABASE_URL="postgresql://your_user:your_password@localhost:5432/your_db_name"
   ```

   **Linux/macOS (bash):**
   ```
   export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/your_db_name"
   ```

**Tip:**  
If `psql` is not recognized, ensure PostgreSQL's `bin` directory is added to your system's PATH environment variable.

---

## Installation

Install all dependencies using the provided `requirements.txt` file:

```
pip install -r requirements.txt
```

---

## Directory Structure

```
csv_loader/
├── data/
│   ├── INFORMATION_SCHEMA.csv
│   ├── ACCOUNTS.csv
│   ├── CHECKING.csv
│   ├── LOANS.csv
│   ├── MEMBERS.csv
│   ├── TRANSACTIONS.csv
│   ├── CUSTOM_FIELDS.csv
│   └── ... (other data files)
├── src/
│   ├── cli.py
│   ├── config.py
│   ├── db.py
│   ├── loader.py
│   ├── queries.py
│   └── schema_builder.py
├── README.md
├── requirements.txt
└── (other project files)
```

---

## Usage

### 1. Create Tables and Load Data

```
python -m src.cli load --schema path/to/INFORMATION_SCHEMA.csv --data-dir path/to/data/
```
- `--schema` (optional): Path to the schema CSV file (default: `data/INFORMATION_SCHEMA.csv`)
- `--data-dir` (optional): Directory containing CSV files (default: `data/`)

### 2. Run Analysis Queries

```
python -m src.cli run-queries
```

---

## Customization

- To add new tables or columns, update `INFORMATION_SCHEMA.csv` and provide matching CSV files.
- To add new queries, edit `src/queries.py` and register them in `src/cli.py`.

---

## Troubleshooting

- **Database connection errors:**  
  Ensure `DATABASE_URL` is set correctly and the database is running.
- **Schema mismatch:**  
  Check that your CSV files match the column names and types defined in `INFORMATION_SCHEMA.csv`.
- **Missing dependencies:**  
  Install required Python packages with `pip install -r requirements.txt`.

---

## Running Tests

This project uses `pytest` for testing. The tests require a PostgreSQL database that is safe to use for testing (tables may be created, modified, or dropped).

### 1. Create a Test Database

Refer to the instructions in **2. Set Up PostgreSQL** above to create a dedicated test database and user.

### 2. Set the TEST_DATABASE_URL Environment Variable

Set the `TEST_DATABASE_URL` environment variable to point to your test database:

**Windows (PowerShell):**
```
$env:TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_db"
```

**Linux/macOS (bash):**
```
export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_db"
```

### 3. Run the Tests

From your project root, run:

```
pytest
```

Pytest will discover and run all tests in the `tests/` directory.

---

**Note:**  
- The test database should be dedicated for testing purposes, as tests may drop or modify tables.
- Ensure all dependencies are installed with `pip install -r requirements.txt` before running tests.

---

## Author

Eric Huber
