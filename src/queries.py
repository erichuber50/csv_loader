from sqlalchemy import text
from .db import get_session

def overdrawn_checking_accounts():
    """
    Return members with overdrawn checking accounts and their balances.

    Returns:
        List of rows, each containing member and account info for overdrawn checking accounts.
    """
    # SQL query to find members whose checking account balance is negative
    query = text("""
        SELECT 
            m."MEMBER_GUID",
            m."FIRST_NAME",
            m."LAST_NAME",
            c."ACCOUNT_GUID",
            (c."STARTING_BALANCE" + COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0)) AS balance
        FROM "CHECKING" c
        JOIN "ACCOUNTS" a ON c."ACCOUNT_GUID" = a."ACCOUNT_GUID"
        JOIN "MEMBERS" m ON a."MEMBER_GUID" = m."MEMBER_GUID"
        LEFT JOIN "TRANSACTIONS" t ON c."ACCOUNT_GUID" = t."ACCOUNT_GUID"
        GROUP BY m."MEMBER_GUID", m."FIRST_NAME", m."LAST_NAME", c."ACCOUNT_GUID", c."STARTING_BALANCE"
        HAVING (c."STARTING_BALANCE" + COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0)) < 0;
    """)
    # Execute the query and return all results
    with get_session() as session:
        return session.execute(query).fetchall()

def overpaid_loans():
    """
    Return members who have overpaid their loans and the overpaid amount.

    Returns:
        List of rows, each containing member and account info for overpaid loans.
    """
    # SQL query to find members who have paid more than their starting loan debt
    query = text("""
        SELECT 
            m."MEMBER_GUID",
            m."FIRST_NAME",
            m."LAST_NAME",
            l."ACCOUNT_GUID",
            (COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0) - l."STARTING_DEBT") AS overpaid_amount
        FROM "LOANS" l
        JOIN "ACCOUNTS" a ON l."ACCOUNT_GUID" = a."ACCOUNT_GUID"
        JOIN "MEMBERS" m ON a."MEMBER_GUID" = m."MEMBER_GUID"
        LEFT JOIN "TRANSACTIONS" t ON l."ACCOUNT_GUID" = t."ACCOUNT_GUID"
        GROUP BY m."MEMBER_GUID", m."FIRST_NAME", m."LAST_NAME", l."ACCOUNT_GUID", l."STARTING_DEBT"
        HAVING COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0) > l."STARTING_DEBT";
    """)
    # Execute the query and return all results
    with get_session() as session:
        return session.execute(query).fetchall()

def total_assets():
    """
    Return the total asset size of the institution (checking balances minus remaining loan debt).

    Returns:
        The total assets as a single numeric value.
    """
    # SQL query to calculate total assets: sum of checking balances minus sum of remaining loan debts
    query = text("""
        WITH checking_balances AS (
            SELECT 
                c."ACCOUNT_GUID",
                (c."STARTING_BALANCE" + COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0)) AS balance
            FROM "CHECKING" c
            LEFT JOIN "TRANSACTIONS" t ON c."ACCOUNT_GUID" = t."ACCOUNT_GUID"
            GROUP BY c."ACCOUNT_GUID", c."STARTING_BALANCE"
        ),
        loan_balances AS (
            SELECT 
                l."ACCOUNT_GUID",
                (l."STARTING_DEBT" - COALESCE(SUM(t."TRANSACTION_AMOUNT"), 0)) AS remaining_debt
            FROM "LOANS" l
            LEFT JOIN "TRANSACTIONS" t ON l."ACCOUNT_GUID" = t."ACCOUNT_GUID"
            GROUP BY l."ACCOUNT_GUID", l."STARTING_DEBT"
        )
        SELECT 
            (COALESCE((SELECT SUM(balance) FROM checking_balances), 0) -
             COALESCE((SELECT SUM(remaining_debt) FROM loan_balances), 0)) AS total_assets;
    """)
    # Execute the query and return the scalar result (total assets)
    with get_session() as session:
        return session.execute(query).scalar_one()
