import os
import tempfile
import shutil
import pytest
import pandas as pd
from sqlalchemy import create_engine

@pytest.fixture(scope="module")
def temp_data_dir():
    """
    Create a temporary data directory with sample CSVs and schema.
    """
    temp_dir = tempfile.mkdtemp()
    schema_path = os.path.join(temp_dir, "INFORMATION_SCHEMA.csv")
    # Minimal schema for testing
    schema_df = pd.DataFrame({
        "TABLE_NAME": ["TEST_TABLE"],
        "COLUMN_NAME": ["ID"],
        "DATA_TYPE": ["numeric"]
    })
    schema_df.to_csv(schema_path, index=False)
    # Sample data file
    data_df = pd.DataFrame({"ID": [1, 2, 3]})
    data_df.to_csv(os.path.join(temp_dir, "TEST_TABLE.csv"), index=False)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="module")
def test_db_url():
    """
    Provide a PostgreSQL test database URL from environment variable TEST_DATABASE_URL.
    The test database should be created and dropped outside of the test run.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL env variable to a PostgreSQL test database URL for these tests.")
    yield url

@pytest.fixture
def engine(test_db_url):
    """
    SQLAlchemy engine for the test database.
    """
    return create_engine(test_db_url, future=True)