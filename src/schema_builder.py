import os
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, DateTime, Text, Numeric
import re
from .config import DEFAULT_DATA_DIR, DEFAULT_SCHEMA_FILE
from sqlalchemy import Numeric

def map_type(dtype: str):
    """
    Map a string data type from the schema CSV to a SQLAlchemy column type.

    Args:
        dtype (str): The data type string from the schema (e.g., 'NUMERIC(38,2)', 'VARCHAR', 'DATE').

    Returns:
        SQLAlchemy type: The corresponding SQLAlchemy column type.
    """
    dtype = dtype.lower().strip()

    if dtype.startswith("numeric"):
        # Handle NUMERIC(precision, scale) like NUMERIC(38,2)
        match = re.search(r"numeric\((\d+)\s*,\s*(\d+)\)", dtype)
        if match:
            precision, scale = map(int, match.groups())
            return Numeric(precision, scale)
        return Numeric

    if "varchar" in dtype or "text" in dtype:
        return String

    if "date" in dtype:
        return Date

    if "timestamp" in dtype:
        return DateTime

    return Text

def create_tables(schema_file: str = DEFAULT_SCHEMA_FILE, engine=None):
    """
    Read a schema CSV file and create tables dynamically in the database.

    Args:
        schema_file (str): Path to the schema CSV file (default: DEFAULT_SCHEMA_FILE).
        engine: SQLAlchemy engine instance. If None, will attempt to create one.

    Returns:
        engine: The SQLAlchemy engine used for table creation.
    """
    if not engine:
        engine = get_engine()

    # Read the schema CSV into a DataFrame
    schema = pd.read_csv(schema_file, skipinitialspace=True, engine="python")

    metadata = MetaData()

    # Group the schema by table name and create each table with its columns
    for table_name, group in schema.groupby("TABLE_NAME"):
        cols = []
        for _, row in group.iterrows():
            # Map the data type and create a SQLAlchemy Column
            col = Column(row["COLUMN_NAME"], map_type(str(row["DATA_TYPE"])))
            cols.append(col)

        # Define the table with its columns
        Table(table_name, metadata, *cols)

    # Drop all existing tables and create new ones as defined in the schema
    metadata.drop_all(engine)
    metadata.create_all(engine)
    print(f"Created tables from {schema_file}")
    return engine