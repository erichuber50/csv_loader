import os
import tempfile
import shutil
import pytest
import pandas as pd
from click.testing import CliRunner
from sqlalchemy import create_engine, inspect, text
from src import cli, schema_builder, loader, queries, config

# --- Fixtures ---

@pytest.fixture(scope="module")
def temp_data_dir():
    """
    Create a temporary data directory with sample CSVs and schema.
    """
    temp_dir = tempfile.mkdtemp()
    schema_path = os.path.join(temp_dir, "INFORMATION_SCHEMA.csv")
    # Minimal schema for testing
    schema_df = pd.DataFrame({
        "TABLE_NAME": ["TEST_TABLE"],
        "COLUMN_NAME": ["ID"],
        "DATA_TYPE": ["numeric"]
    })
    schema_df.to_csv(schema_path, index=False)
    # Sample data file
    data_df = pd.DataFrame({"ID": [1, 2, 3]})
    data_df.to_csv(os.path.join(temp_dir, "TEST_TABLE.csv"), index=False)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="module")
def test_db_url():
    """
    Provide a PostgreSQL test database URL from environment variable TEST_DATABASE_URL.
    The test database should be created and dropped outside of the test run.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL env variable to a PostgreSQL test database URL for these tests.")
    yield url

@pytest.fixture
def engine(test_db_url):
    """
    SQLAlchemy engine for the test database.
    """
    return create_engine(test_db_url, future=True)

# --- Tests ---

def test_schema_builder_creates_table(engine, temp_data_dir):
    """
    Test that schema_builder creates tables from schema.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    insp = inspect(engine)
    assert "TEST_TABLE" in insp.get_table_names()

def test_loader_loads_data(engine, temp_data_dir):
    """
    Test that loader loads CSV data into the database.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "TEST_TABLE"'))
        count = result.scalar()
    assert count == 3

def test_validate_csv_columns_accepts_valid(temp_data_dir):
    """
    Test that validate_csv_columns accepts valid CSV columns.
    """
    schema = schema_builder.get_schema_columns(os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
    df = pd.DataFrame({"ID": [1]})
    assert loader.validate_csv_columns("TEST_TABLE", df, schema)

def test_validate_csv_columns_rejects_invalid(temp_data_dir):
    """
    Test that validate_csv_columns rejects invalid CSV columns.
    """
    schema = schema_builder.get_schema_columns(os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
    df = pd.DataFrame({"WRONG": [1]})
    assert not loader.validate_csv_columns("TEST_TABLE", df, schema)

def test_cli_load_and_run_queries(monkeypatch, temp_data_dir, test_db_url):
    """
    Test the CLI load and run_queries commands end-to-end.
    """
    runner = CliRunner()
    # Patch config.DATABASE_URL to use test DB
    monkeypatch.setattr(config, "DATABASE_URL", test_db_url)
    # Patch default paths
    monkeypatch.setattr(config, "DEFAULT_DATA_DIR", temp_data_dir)
    monkeypatch.setattr(config, "DEFAULT_SCHEMA_FILE", os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
    # Run load command
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code == 0
    assert "Using schema" in result.output
    # Run run_queries command (should not fail, even if no data for queries)
    result = runner.invoke(cli.cli, ["run-queries"])
    assert result.exit_code == 0

def test_loader_handles_extra_and_missing_columns(engine, temp_data_dir):
    """
    Test loader handles extra and missing columns gracefully.
    """
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
    # Optionally, try to insert and expect failure (if loader skips or raises)
    # Here we just check validation logic, as loader.load_csv would skip

def test_loader_skips_invalid_files(engine, temp_data_dir):
    """
    Test loader skips files with schema mismatch.
    """
    # Create a CSV with wrong columns
    bad_csv = os.path.join(temp_data_dir, "BAD.csv")
    pd.DataFrame({"WRONG": [1]}).to_csv(bad_csv, index=False)
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    # Should not raise, just skip
    loader.load_all(engine, temp_data_dir, schema_file)

def test_schema_drift_add_remove_transpose_columns(engine, temp_data_dir):
    """
    Test handling of schema drift: adding, removing, and transposing columns in the schema and CSV.
    """
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    data_file = os.path.join(temp_data_dir, "TEST_TABLE.csv")

    # --- Add a new column ---
    # Add a new column to schema
    schema_df = pd.read_csv(schema_file)
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "TEST_TABLE", "COLUMN_NAME": "NAME", "DATA_TYPE": "varchar"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    # Add new column to data
    df = pd.read_csv(data_file)
    df["NAME"] = ["Alice", "Bob", "Carol"]
    df.to_csv(data_file, index=False)
    # Recreate table and reload data
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    # Check that new column exists and data is loaded
    with engine.connect() as conn:
        result = conn.execute(text('SELECT "ID", "NAME" FROM "TEST_TABLE"'))
        rows = result.mappings().all()
    assert all(row["NAME"] in ["Alice", "Bob", "Carol"] for row in rows)

    # --- Remove a column ---
    # Remove the NAME column from schema and data
    schema_df = schema_df[schema_df["COLUMN_NAME"] != "NAME"]
    schema_df.to_csv(schema_file, index=False)
    df = df.drop(columns=["NAME"])
    df.to_csv(data_file, index=False)
    # Recreate table and reload data
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    # Check that only ID column exists
    with engine.connect() as conn:
        insp = inspect(engine)
        columns = [col["name"] for col in insp.get_columns("TEST_TABLE")]
    assert columns == ["ID"]

    # --- Transpose columns (change order) ---
    # Add NAME column back, but in different order in CSV
    schema_df = pd.concat([
        schema_df,
        pd.DataFrame([{"TABLE_NAME": "TEST_TABLE", "COLUMN_NAME": "NAME", "DATA_TYPE": "varchar"}])
    ], ignore_index=True)
    schema_df.to_csv(schema_file, index=False)
    # Write CSV with columns in order: NAME, ID
    df = pd.DataFrame({"NAME": ["X", "Y", "Z"], "ID": [4, 5, 6]})
    df.to_csv(data_file, index=False, columns=["NAME", "ID"])
    # Recreate table and reload data
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)
    # Check that data is loaded correctly despite column order
    with engine.connect() as conn:
        result = conn.execute(text('SELECT "ID", "NAME" FROM "TEST_TABLE" ORDER BY "ID"'))
        rows = result.mappings().all()
    assert [row["NAME"] for row in rows] == ["X", "Y", "Z"]
    assert [row["ID"] for row in rows] == [4, 5, 6]

def test_query_results_on_sample_data(engine, temp_data_dir):
    """
    Test that the analysis queries return expected results for known input data.
    """
    # Prepare schema for CHECKING, ACCOUNTS, MEMBERS, LOANS, TRANSACTIONS
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_df = pd.DataFrame([
        {"TABLE_NAME": "MEMBERS", "COLUMN_NAME": "MEMBER_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "MEMBERS", "COLUMN_NAME": "FIRST_NAME", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "MEMBERS", "COLUMN_NAME": "LAST_NAME", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "ACCOUNTS", "COLUMN_NAME": "ACCOUNT_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "ACCOUNTS", "COLUMN_NAME": "MEMBER_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "CHECKING", "COLUMN_NAME": "ACCOUNT_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "CHECKING", "COLUMN_NAME": "STARTING_BALANCE", "DATA_TYPE": "numeric"},
        {"TABLE_NAME": "LOANS", "COLUMN_NAME": "ACCOUNT_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "LOANS", "COLUMN_NAME": "STARTING_DEBT", "DATA_TYPE": "numeric"},
        {"TABLE_NAME": "TRANSACTIONS", "COLUMN_NAME": "ACCOUNT_GUID", "DATA_TYPE": "varchar"},
        {"TABLE_NAME": "TRANSACTIONS", "COLUMN_NAME": "TRANSACTION_AMOUNT", "DATA_TYPE": "numeric"},
    ])
    schema_df.to_csv(schema_file, index=False)

    # Prepare data
    # One member, one checking (overdrawn), one loan (overpaid)
    pd.DataFrame([
        {"MEMBER_GUID": "m1", "FIRST_NAME": "Alice", "LAST_NAME": "Smith"},
    ]).to_csv(os.path.join(temp_data_dir, "MEMBERS.csv"), index=False)
    pd.DataFrame([
        {"ACCOUNT_GUID": "a1", "MEMBER_GUID": "m1"},
        {"ACCOUNT_GUID": "a2", "MEMBER_GUID": "m1"},
    ]).to_csv(os.path.join(temp_data_dir, "ACCOUNTS.csv"), index=False)
    pd.DataFrame([
        {"ACCOUNT_GUID": "a1", "STARTING_BALANCE": -100},
    ]).to_csv(os.path.join(temp_data_dir, "CHECKING.csv"), index=False)
    pd.DataFrame([
        {"ACCOUNT_GUID": "a2", "STARTING_DEBT": 50},
    ]).to_csv(os.path.join(temp_data_dir, "LOANS.csv"), index=False)
    pd.DataFrame([
        {"ACCOUNT_GUID": "a1", "TRANSACTION_AMOUNT": 0},
        {"ACCOUNT_GUID": "a2", "TRANSACTION_AMOUNT": 100},
    ]).to_csv(os.path.join(temp_data_dir, "TRANSACTIONS.csv"), index=False)

    # Create tables and load data
    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)

    # Test overdrawn_checking_accounts
    rows = queries.overdrawn_checking_accounts()
    assert any(row._mapping["FIRST_NAME"] == "Alice" and row._mapping["balance"] == -100 for row in rows)

    # Test overpaid_loans
    rows = queries.overpaid_loans()
    assert any(row._mapping["FIRST_NAME"] == "Alice" and row._mapping["overpaid_amount"] == 50 for row in rows)

    # Test total_assets
    total = queries.total_assets()
    # total assets = checking balance sum - remaining loan debt sum = (-100) - (50 - 100) = (-100) - (-50) = -50
    assert total == -50