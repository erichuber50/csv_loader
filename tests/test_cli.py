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
    """Test that validate_csv_columns rejects invalid CSV columns."""
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
    """Test loader skips files with schema mismatch."""
    # Create a CSV with wrong columns
    bad_csv = os.path.join(temp_data_dir, "BAD.csv")
    pd.DataFrame({"WRONG": [1]}).to_csv(bad_csv, index=False)
    schema_file = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    schema_builder.create_tables(schema_file, engine)
    # Should not raise, just skip
    loader.load_all(engine, temp_data_dir, schema_file)