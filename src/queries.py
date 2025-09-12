from sqlalchemy import text
from .db import get_session

def overdrawn_checking_accounts():
    """Return members with overdrawn checking accounts and balances."""
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
    with get_session() as session:
        return session.execute(query).fetchall()

def overpaid_loans():
    """Return members who overpaid their loans and the overpaid amount."""
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
    with get_session() as session:
        return session.execute(query).fetchall()

def total_assets():
    """Return the total asset size of the institution (checking - loan debt)."""
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
    with get_session() as session:
        return session.execute(query).scalar_one()
