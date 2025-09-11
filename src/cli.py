import os
import click
from . import schema_builder, loader, queries
from .config import DEFAULT_DATA_DIR, DEFAULT_SCHEMA_FILE
from .db import get_engine, get_session
from sqlalchemy import text

@click.group()
def cli():
    """Command-line interface for the Data Loader app."""
    pass

@cli.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    default=DEFAULT_SCHEMA_FILE,
    show_default=True,
    help="Path to INFORMATION_SCHEMA.csv"
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True),
    default=DEFAULT_DATA_DIR,
    show_default=True,
    help="Directory containing CSV files to load"
)
def load(schema, data_dir):
    """Create tables from schema and load CSV data into the database."""
    click.echo(f"Using schema: {schema}")
    click.echo(f"Loading CSVs from: {data_dir}")

    # Create DB engine/session
    engine = get_engine()

    # Create DB schema
    schema_builder.create_tables(schema, engine)

    # Load CSVs
    loader.load_all(engine, data_dir)

@cli.command()
def run_queries():
    """Run analysis queries and print results."""
    click.echo("Overdrawn Checking Accounts:")
    for row in queries.overdrawn_checking_accounts():
        click.echo(dict(row._mapping))

    click.echo("\nOverpaid Loans:")
    for row in queries.overpaid_loans():
        click.echo(dict(row._mapping))

    click.echo("\nTotal Assets:")
    click.echo(queries.total_assets())

if __name__ == "__main__":
    cli()
