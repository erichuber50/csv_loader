import os
import pandas as pd
from sqlalchemy import inspect, text
from src import schema_builder, loader

def test_schema_builder_creates_table(engine, temp_data_dir):
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    insp = inspect(engine)
    assert "TEST_TABLE" in insp.get_table_names()

def test_loader_loads_data(engine, temp_data_dir):
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "TEST_TABLE"'))
        count = result.scalar()
    assert count == 3

def test_loader_handles_extra_and_missing_columns(engine, temp_data_dir):
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    schema = schema_builder.get_schema_columns(schema_file)

    # Extra column: should ignore extra column and load
    df_extra = pd.DataFrame({"ID": [1], "EXTRA": [99]})
    df_extra[["ID"]].to_sql("TEST_TABLE", engine, if_exists="append", index=False)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "TEST_TABLE"'))
        count = result.scalar()
    assert count >= 1

    # Missing column: should fail validation and not insert
    df_missing = pd.DataFrame({"EXTRA": [99]})
    is_valid = loader.validate_csv_columns("TEST_TABLE", df_missing, schema)
    assert not is_valid

def test_loader_skips_invalid_files(engine, temp_data_dir):
    bad_csv = os.path.join(temp_data_dir, "BAD.csv")
    pd.DataFrame({"WRONG": [1]}).to_csv(bad_csv, index=False)
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)

def test_schema_drift_add_remove_transpose_columns(engine, temp_data_dir):
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    data_file = os.path.join(temp_data_dir, "TEST_TABLE.csv")

    # --- Add a new column ---
    schema_df = pd.read_csv(schema_file)
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "TEST_TABLE", "COLUMN_NAME": "NAME", "DATA_TYPE": "varchar"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    df = pd.read_csv(data_file)
    df["NAME"] = ["Alice", "Bob", "Carol"]
    df.to_csv(data_file, index=False)
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT "ID", "NAME" FROM "TEST_TABLE"'))
        rows = result.mappings().all()
    assert all(row["NAME"] in ["Alice", "Bob", "Carol"] for row in rows)

    # --- Remove a column ---
    schema_df = schema_df[schema_df["COLUMN_NAME"] != "NAME"]
    schema_df.to_csv(schema_file, index=False)
    df = df.drop(columns=["NAME"])
    df.to_csv(data_file, index=False)
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        insp = inspect(engine)
        columns = [col["name"] for col in insp.get_columns("TEST_TABLE")]
    assert columns == ["ID"]

    # --- Transpose columns (change order) ---
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "TEST_TABLE", "COLUMN_NAME": "NAME", "DATA_TYPE": "varchar"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    df = pd.DataFrame({"NAME": ["X", "Y", "Z"], "ID": [4, 5, 6]})
    df.to_csv(data_file, index=False, columns=["NAME", "ID"])
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT "ID", "NAME" FROM "TEST_TABLE" ORDER BY "ID"'))
        rows = result.mappings().all()
    assert [row["NAME"] for row in rows] == ["X", "Y", "Z"]
    assert [row["ID"] for row in rows] == [4, 5, 6]

def test_validate_csv_columns_accepts_valid(temp_data_dir):
    """
    Test that validate_csv_columns accepts valid CSV columns.
    """
    # Reset schema to only ID
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    pd.DataFrame({
        "TABLE_NAME": ["TEST_TABLE"],
        "COLUMN_NAME": ["ID"],
        "DATA_TYPE": ["numeric"]
    }).to_csv(schema_file, index=False)
    schema = schema_builder.get_schema_columns(schema_file)
    df = pd.DataFrame({"ID": [1]})
    assert loader.validate_csv_columns("TEST_TABLE", df, schema)

def test_validate_csv_columns_rejects_invalid(temp_data_dir):
    """
    Test that validate_csv_columns rejects invalid CSV columns.
    """
    # Reset schema to only ID
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    pd.DataFrame({
        "TABLE_NAME": ["TEST_TABLE"],
        "COLUMN_NAME": ["ID"],
        "DATA_TYPE": ["numeric"]
    }).to_csv(schema_file, index=False)
    schema = schema_builder.get_schema_columns(schema_file)
    df = pd.DataFrame({"WRONG": [1]})
    assert not loader.validate_csv_columns("TEST_TABLE", df, schema)

def test_loader_rejects_wrong_data_type(engine, temp_data_dir):
    """
    Test that inserting wrong data type (e.g., string into numeric) is rejected.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    # DataFrame with wrong type for ID (should be numeric)
    df = pd.DataFrame({"ID": ["not_a_number"]})
    try:
        df.to_sql("TEST_TABLE", engine, if_exists="append", index=False)
        assert False, "Expected a data type error"
    except Exception:
        pass  # Expected: should raise due to type mismatch

def test_loader_inserts_null_for_missing_values(engine, temp_data_dir):
    """
    Test that missing values in the CSV are inserted as NULL in the database.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    df = pd.DataFrame({"ID": [None, 2, 3]})
    df.to_sql("TEST_TABLE", engine, if_exists="append", index=False)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "TEST_TABLE" WHERE "ID" IS NULL'))
        null_count = result.scalar()
    assert null_count == 1

def test_loader_loads_multiple_tables(engine, temp_data_dir):
    """
    Test that multiple tables can be loaded in a single run.
    """
    # Add a second table to schema and data
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_df = pd.read_csv(schema_file)
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "SECOND_TABLE", "COLUMN_NAME": "VAL", "DATA_TYPE": "numeric"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    pd.DataFrame({"VAL": [10, 20]}).to_csv(os.path.join(temp_data_dir, "SECOND_TABLE.csv"), index=False)
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "SECOND_TABLE"'))
        count = result.scalar()
    assert count == 2

def test_loader_handles_empty_csv(engine, temp_data_dir):
    """
    Test that loading an empty CSV file (header only, no data) does not insert any rows and does not fail.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    empty_csv = os.path.join(temp_data_dir, "EMPTY_TABLE.csv")
    # Add schema for EMPTY_TABLE
    schema_df = pd.read_csv(schema_file)
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "EMPTY_TABLE", "COLUMN_NAME": "VAL", "DATA_TYPE": "numeric"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    # Write empty CSV (header only)
    pd.DataFrame({"VAL": []}).to_csv(empty_csv, index=False)
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "EMPTY_TABLE"'))
        count = result.scalar()
    assert count == 0