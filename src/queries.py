from sqlalchemy import text
from .db import get_session

def overdrawn_checking_accounts():
    """Return members with overdrawn checking accounts and balances."""
    query = text("""
        SELECT 
            m.member_guid,
            m.first_name,
            m.last_name,
            c.account_guid,
            (c.starting_balance + COALESCE(SUM(t.transaction_amount), 0)) AS balance
        FROM checking c
        JOIN accounts a ON c.account_guid = a.account_guid
        JOIN members m ON a.member_guid = m.member_guid
        LEFT JOIN transactions t ON c.account_guid = t.account_guid
        GROUP BY m.member_guid, m.first_name, m.last_name, c.account_guid, c.starting_balance
        HAVING (c.starting_balance + COALESCE(SUM(t.transaction_amount), 0)) < 0;
    """)
    with get_session() as session:
        return session.execute(query).fetchall()


def overpaid_loans():
    """Return members who overpaid their loans and the overpaid amount."""
    query = text("""
        SELECT 
            m.member_guid,
            m.first_name,
            m.last_name,
            l.account_guid,
            (COALESCE(SUM(t.transaction_amount), 0) - l.starting_debt) AS overpaid_amount
        FROM loans l
        JOIN accounts a ON l.account_guid = a.account_guid
        JOIN members m ON a.member_guid = m.member_guid
        LEFT JOIN transactions t ON l.account_guid = t.account_guid
        GROUP BY m.member_guid, m.first_name, m.last_name, l.account_guid, l.starting_debt
        HAVING COALESCE(SUM(t.transaction_amount), 0) > l.starting_debt;
    """)
    with get_session() as session:
        return session.execute(query).fetchall()


def total_assets():
    """Return the total asset size of the institution (checking - loan debt)."""
    query = text("""
        WITH checking_balances AS (
            SELECT 
                c.account_guid,
                (c.starting_balance + COALESCE(SUM(t.transaction_amount), 0)) AS balance
            FROM checking c
            LEFT JOIN transactions t ON c.account_guid = t.account_guid
            GROUP BY c.account_guid, c.starting_balance
        ),
        loan_balances AS (
            SELECT 
                l.account_guid,
                (l.starting_debt - COALESCE(SUM(t.transaction_amount), 0)) AS remaining_debt
            FROM loans l
            LEFT JOIN transactions t ON l.account_guid = t.account_guid
            GROUP BY l.account_guid, l.starting_debt
        )
        SELECT 
            (COALESCE((SELECT SUM(balance) FROM checking_balances), 0) -
             COALESCE((SELECT SUM(remaining_debt) FROM loan_balances), 0)) AS total_assets;
    """)
    with get_session() as session:
        return session.execute(query).scalar_one()
