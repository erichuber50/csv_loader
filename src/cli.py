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
    """
    Create tables from schema and load data into database.
    
    Args:
        schema (str): Path to the schema CSV file.
        data_dir (str): Directory containing CSV files to load.
    """
    click.echo(f"Using schema: {schema}")
    click.echo(f"Loading CSVs from: {data_dir}")

    # Create DB engine/session
    engine = get_engine()

    # Create DB tables from schema file
    schema_builder.create_tables(schema, engine)

    # Load all CSV files from the data directory into the database
    loader.load_all(engine, data_dir)

@cli.command()
def run_queries():
    """
    Run analysis queries and print results.
    """
    click.echo("Overdrawn Checking Accounts:")
    rows = queries.overdrawn_checking_accounts()
    if rows:
        for row in rows:
            data = row._mapping
            # Print member and account info for overdrawn checking accounts
            click.echo(
                f"Member: {data['FIRST_NAME']} {data['LAST_NAME']} | "
                f"Account: {data['ACCOUNT_GUID']} | "
                f"Balance: {data['balance']}"
            )
    else:
        click.echo("None found.")

    click.echo("\nOverpaid Loans:")
    rows = queries.overpaid_loans()
    if rows:
        for row in rows:
            data = row._mapping
            # Print member and account info for overpaid loans
            click.echo(
                f"Member: {data['FIRST_NAME']} {data['LAST_NAME']} | "
                f"Account: {data['ACCOUNT_GUID']} | "
                f"Overpaid Amount: {data['overpaid_amount']}"
            )
    else:
        click.echo("None found.")

    click.echo("\nTotal Assets:")
    # Print the total assets of the institution
    click.echo(f"{queries.total_assets():,.2f}")

if __name__ == "__main__":
    # Entry point for running the CLI directly
    cli()
