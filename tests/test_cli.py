import os
from click.testing import CliRunner
from src import cli, config

def test_cli_load_and_run_queries(temp_data_dir):
    """
    Test the CLI load and run_queries commands end-to-end.
    """
    runner = CliRunner()
    config.DEFAULT_DATA_DIR = temp_data_dir
    config.DEFAULT_SCHEMA_FILE = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code == 0
    assert "Using schema" in result.output
    result = runner.invoke(cli.cli, ["run-queries"])
    assert result.exit_code == 0

def test_cli_load_db_error(monkeypatch, temp_data_dir):
    """
    Test that the CLI load command handles database connection errors gracefully.
    """
    runner = CliRunner()
    # Patch get_engine to raise an exception
    monkeypatch.setattr("src.cli.get_engine", lambda: (_ for _ in ()).throw(Exception("DB connection failed")))
    config.DEFAULT_DATA_DIR = temp_data_dir
    config.DEFAULT_SCHEMA_FILE = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code != 0
    assert "Error connecting to the database" in result.output

def test_cli_load_schema_error(monkeypatch, temp_data_dir):
    """
    Test that the CLI load command handles schema creation errors gracefully.
    """
    runner = CliRunner()
    # Patch get_engine to return a valid engine
    from sqlalchemy import create_engine
    monkeypatch.setattr("src.cli.get_engine", lambda: create_engine(os.environ["TEST_DATABASE_URL"], future=True))
    # Patch schema_builder.create_tables to raise an exception
    monkeypatch.setattr("src.cli.schema_builder.create_tables", lambda schema, engine: (_ for _ in ()).throw(Exception("Schema error")))
    config.DEFAULT_DATA_DIR = temp_data_dir
    config.DEFAULT_SCHEMA_FILE = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code != 0
    assert "Error creating tables from schema" in result.output

def test_cli_load_loader_error(monkeypatch, temp_data_dir):
    """
    Test that the CLI load command handles loader errors gracefully.
    """
    runner = CliRunner()
    from sqlalchemy import create_engine
    monkeypatch.setattr("src.cli.get_engine", lambda: create_engine(os.environ["TEST_DATABASE_URL"], future=True))
    # Patch schema_builder.create_tables to do nothing
    monkeypatch.setattr("src.cli.schema_builder.create_tables", lambda schema, engine: None)
    # Patch loader.load_all to raise an exception
    monkeypatch.setattr("src.cli.loader.load_all", lambda engine, data_dir: (_ for _ in ()).throw(Exception("Loader error")))
    config.DEFAULT_DATA_DIR = temp_data_dir
    config.DEFAULT_SCHEMA_FILE = os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv")
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code != 0
    assert "Error loading CSV files" in result.output

def test_cli_run_queries_error(monkeypatch, temp_data_dir):
    """
    Test that the CLI run_queries command handles errors gracefully.
    """
    runner = CliRunner()
    # Patch queries.overdrawn_checking_accounts to raise an exception
    monkeypatch.setattr("src.cli.queries.overdrawn_checking_accounts", lambda: (_ for _ in ()).throw(Exception("Query error")))
    result = runner.invoke(cli.cli, ["run-queries"])
    assert result.exit_code != 0
    assert "Error running queries: Query error" in result.output