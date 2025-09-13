import os
import pandas as pd
from sqlalchemy import text
from .config import DEFAULT_DATA_DIR, DEFAULT_SCHEMA_FILE
from .schema_builder import get_schema_columns

def validate_csv_columns(table_name, df, schema):
    """
    Validate that the DataFrame columns match the expected schema columns, ignoring order and extra columns.

    Args:
        table_name (str): Name of the table being loaded.
        df (pd.DataFrame): DataFrame loaded from the CSV file.
        schema (dict): Mapping of table names to expected column lists.

    Returns:
        bool: True if columns match the schema, False otherwise.
    """
    expected_cols = schema.get(table_name)
    if expected_cols is None:
        # No schema is found for the table
        print(f"No schema found for table '{table_name}'.")
        return False
    csv_cols = list(df.columns)
    missing = [col for col in expected_cols if col not in csv_cols]
    extra = [col for col in csv_cols if col not in expected_cols]
    if missing:
        # Print details if columns are missing
        print(f"Missing columns for table '{table_name}': {missing}")
    if extra:
        # Print details if there are extra columns in the CSV
        print(f"Extra columns in CSV for table '{table_name}': {extra}")
    # Only fail if required columns are missing
    return not missing

def load_csv(engine, table_name, file_path, schema=None):
    """
    Load a single CSV file into a specified database table, with schema validation.

    Args:
        engine: SQLAlchemy engine instance connected to the target database.
        table_name (str): Name of the table to insert data into.
        file_path (str): Path to the CSV file to be loaded.
        schema (dict, optional): Schema definition for validation (default: None).

    Returns:
        None
    """
    df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
    if schema is not None:
        # Validate columns before loading
        if not validate_csv_columns(table_name, df, schema):
            print(f"Skipping {file_path} due to schema mismatch.\n")
            return
        # Reorder and add missing columns as NaN
        expected_cols = schema.get(table_name)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[expected_cols]  # Reorder columns
    # Insert the DataFrame into the specified table, appending rows
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"Inserted {len(df)} rows into {table_name}")

    # Verify insertion by counting rows in the database
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        db_count = result.scalar()

    if db_count >= len(df):
        print(f"Verification: {db_count} total rows in '{table_name}' after insert (expected at least {len(df)}).\n")
    
    else:
        print(f"Warning: Only {db_count} rows in '{table_name}' after insert (expected at least {len(df)}).\n")

def load_all(engine, data_dir: str = DEFAULT_DATA_DIR, schema_file: str = DEFAULT_SCHEMA_FILE):
    """
    Load all CSV files from a directory into their corresponding database tables, with schema validation.

    Args:
        engine: SQLAlchemy engine instance connected to the target database.
        data_dir (str): Directory containing CSV files to load (default: DEFAULT_DATA_DIR).
        schema_file (str): Path to the schema file for validation (default: DEFAULT_SCHEMA_FILE).

    Returns:
        None
    """
    schema = get_schema_columns(schema_file)  # Load schema definitions
    # Iterate over all files in the data directory
    for file in os.listdir(data_dir):
        # Only process CSV files, skip the schema definition file
        if file.lower().endswith(".csv") and file != "INFORMATION_SCHEMA.csv":
            table_name = os.path.splitext(file)[0]  # Use filename (without extension) as table name
            path = os.path.join(data_dir, file)     # Full path to the CSV file
            print("Loading:", table_name, path)
            try:
                # Attempt to load the CSV into the table with schema validation
                load_csv(engine, table_name, path, schema)
            except Exception as e:
                # Print error and skip file on failure
                print(f"Skipping {file}: {e}")