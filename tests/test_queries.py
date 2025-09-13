import os
import pandas as pd
from src import schema_builder, loader, queries

def test_query_results_on_sample_data(engine, temp_data_dir):
    """
    Test that the analysis queries return expected results for known input data.
    """
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

    schema_builder.create_tables(schema_file, engine)
    loader.load_all(engine, temp_data_dir, schema_file)

    rows = queries.overdrawn_checking_accounts()
    assert any(row._mapping["FIRST_NAME"] == "Alice" and row._mapping["balance"] == -100 for row in rows)

    rows = queries.overpaid_loans()
    assert any(row._mapping["FIRST_NAME"] == "Alice" and row._mapping["overpaid_amount"] == 50 for row in rows)

    total = queries.total_assets()
    assert total == -50