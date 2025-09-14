import sys
import os
import click
from . import schema_builder, loader, queries
from .config import DEFAULT_DATA_DIR, DEFAULT_SCHEMA_FILE
from .db import get_engine, get_session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

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
    """
    click.echo(f"Using schema: {schema}")
    click.echo(f"Loading CSVs from: {data_dir}")

    try:
        engine = get_engine()
    except Exception as e:
        click.secho(f"Error connecting to the database: {e}", fg="red", err=True)
        sys.exit(1)

    try:
        schema_builder.create_tables(schema, engine)
    except Exception as e:
        click.secho(f"Error creating tables from schema: {e}", fg="red", err=True)
        sys.exit(1)

    try:
        loader.load_all(engine, data_dir)
    except Exception as e:
        click.secho(f"Error loading CSV files: {e}", fg="red", err=True)
        sys.exit(1)

    click.secho("Data loading completed successfully.", fg="green")

@cli.command()
def run_queries():
    """
    Run analysis queries and print results.
    """
    try:
        click.echo("Overdrawn Checking Accounts:")
        rows = queries.overdrawn_checking_accounts()
        if rows:
            for row in rows:
                data = row._mapping
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
                click.echo(
                    f"Member: {data['FIRST_NAME']} {data['LAST_NAME']} | "
                    f"Account: {data['ACCOUNT_GUID']} | "
                    f"Overpaid Amount: {data['overpaid_amount']}"
                )
        else:
            click.echo("None found.")

        click.echo("\nTotal Assets:")
        click.echo(f"{queries.total_assets():,.2f}")
    except ProgrammingError as e:
        if "does not exist" in str(e):
            click.secho(
                "Database tables do not exist. Please run the 'load' command first.",
                fg="red", err=True
            )
        else:
            click.secho(f"Error running queries: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error running queries: {e}", fg="red", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()
