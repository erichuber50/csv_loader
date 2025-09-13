import os
from click.testing import CliRunner
from src import cli, config

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

def test_cli_load_db_error(monkeypatch, temp_data_dir):
    """
    Test that the CLI load command handles database connection errors gracefully.
    """
    runner = CliRunner()
    # Patch get_engine to raise an exception
    monkeypatch.setattr("src.cli.get_engine", lambda: (_ for _ in ()).throw(Exception("DB connection failed")))
    # Patch default paths
    monkeypatch.setattr(config, "DEFAULT_DATA_DIR", temp_data_dir)
    monkeypatch.setattr(config, "DEFAULT_SCHEMA_FILE", os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code != 0
    assert "Error connecting to the database" in result.output

def test_cli_load_schema_error(monkeypatch, temp_data_dir, test_db_url):
    """
    Test that the CLI load command handles schema creation errors gracefully.
    """
    runner = CliRunner()
    # Patch get_engine to return a valid engine
    monkeypatch.setattr("src.cli.get_engine", lambda: __import__("sqlalchemy").create_engine(test_db_url, future=True))
    # Patch schema_builder.create_tables to raise an exception
    monkeypatch.setattr("src.cli.schema_builder.create_tables", lambda schema, engine: (_ for _ in ()).throw(Exception("Schema error")))
    monkeypatch.setattr(config, "DEFAULT_DATA_DIR", temp_data_dir)
    monkeypatch.setattr(config, "DEFAULT_SCHEMA_FILE", os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code != 0
    assert "Error creating tables from schema" in result.output

def test_cli_load_loader_error(monkeypatch, temp_data_dir, test_db_url):
    """
    Test that the CLI load command handles loader errors gracefully.
    """
    runner = CliRunner()
    # Patch get_engine to return a valid engine
    monkeypatch.setattr("src.cli.get_engine", lambda: __import__("sqlalchemy").create_engine(test_db_url, future=True))
    # Patch schema_builder.create_tables to do nothing
    monkeypatch.setattr("src.cli.schema_builder.create_tables", lambda schema, engine: None)
    # Patch loader.load_all to raise an exception
    monkeypatch.setattr("src.cli.loader.load_all", lambda engine, data_dir: (_ for _ in ()).throw(Exception("Loader error")))
    monkeypatch.setattr(config, "DEFAULT_DATA_DIR", temp_data_dir)
    monkeypatch.setattr(config, "DEFAULT_SCHEMA_FILE", os.path.join(temp_data_dir, "INFORMATION_SCHEMA.csv"))
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