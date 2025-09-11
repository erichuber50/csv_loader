import os
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, DateTime, Text, Numeric
import re
from .config import DEFAULT_DATA_DIR, DEFAULT_SCHEMA_FILE
from sqlalchemy import Numeric

def map_type(dtype: str):
    dtype = dtype.lower().strip()
    if dtype.startswith("numeric"):
        # Handle NUMERIC(precision, scale) like NUMERIC(38,2)
        import re
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
    """Read INFORMATION_SCHEMA.csv and create tables dynamically."""
    if not engine:
        engine = get_engine()

    schema = pd.read_csv(schema_file, skipinitialspace=True, engine="python")

    metadata = MetaData()

    for table_name, group in schema.groupby("TABLE_NAME"):
        cols = []
        for _, row in group.iterrows():
            col = Column(row["COLUMN_NAME"].lower(), map_type(str(row["DATA_TYPE"])))
            cols.append(col)

        Table(table_name.lower(), metadata, *cols)

    metadata.drop_all(engine)   # Drop existing tables to start fresh
    metadata.create_all(engine)
    print(f"Created tables from {schema_file}")
    return engine