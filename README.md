# README.txt

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

- **Proven Data Integrity:**  
  Verifies that all records in a given file have been successfully inserted into the database.

- **Schema Drift Handling:**  
  Accounts for changes in the files over time, including column additions, removals, and column order changes.

---

## Requirements

- Python 3.8+
- PostgreSQL database
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [pandas](https://pandas.pydata.org/)
- [Click](https://click.palletsprojects.com/)

Install dependencies with:
```
pip install sqlalchemy pandas click
```

---

## Configuration

Set the `DATABASE_URL` environment variable to your PostgreSQL connection string, for example:

**Windows (PowerShell):**
```
$env:DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
```

**Linux/macOS (bash):**
```
export DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
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
  Install required Python packages with `pip install sqlalchemy pandas click`.

---

## Author

Eric Huber
