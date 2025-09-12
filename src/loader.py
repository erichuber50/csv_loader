import os
import pandas as pd
from sqlalchemy import text
from .config import DEFAULT_DATA_DIR

def load_csv(engine, table_name, file_path):
    """Load one CSV into a table."""
    df = pd.read_csv(file_path)

    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"Inserted {len(df)} rows into {table_name}")

def load_all(engine, data_dir: str = DEFAULT_DATA_DIR):
    """Load all CSVs from a directory into matching tables."""
    for file in os.listdir(data_dir):
        if file.lower().endswith(".csv") and file != "INFORMATION_SCHEMA.csv":
            table_name = os.path.splitext(file)[0]
            path = os.path.join(data_dir, file)
            print("Loading:", table_name, path)
            try:
                load_csv(engine, table_name, path)
            except Exception as e:
                print(f"Skipping {file}: {e}")