import os

# DEFAULT_DATA_DIR points to the "data" directory located one level above this file's directory.
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# DEFAULT_SCHEMA_FILE points to the INFORMATION_SCHEMA.csv file inside the default data directory.
DEFAULT_SCHEMA_FILE = os.path.join(DEFAULT_DATA_DIR, "INFORMATION_SCHEMA.csv")

# Get the database URL from an environment variable.
DATABASE_URL = os.getenv("DATABASE_URL")