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