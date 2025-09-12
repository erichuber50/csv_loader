# README.md

## CSV Loader

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
2. Create a new database and user:
    ```
    -- In psql or your SQL client:
    CREATE DATABASE your_db_name;
    CREATE USER your_user WITH PASSWORD 'your_password';
    GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_user;
    ```

---

## Installation

Install all dependencies using the provided `requirements.txt` file:

```
pip install -r requirements.txt
```

---

## Configuration

Set the `DATABASE_URL` environment variable to your PostgreSQL connection string, for example:

**Windows (PowerShell):**
```
$env:DATABASE_URL="postgresql://your_user:your_password@localhost:5432/your_db_name"
```

**Linux/macOS (bash):**
```
export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/your_db_name"
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

## Author

Eric Huber
