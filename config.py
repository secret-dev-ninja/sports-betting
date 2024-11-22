import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Parse DATABASE_URL for Heroku
database_url = os.getenv('DATABASE_URL')

result = urlparse(database_url)
DB_CONFIG = {
    'dbname': result.path[1:],
    'user': result.username,
    'password': result.password,
    'host': result.hostname,
    'port': result.port or 5432
}