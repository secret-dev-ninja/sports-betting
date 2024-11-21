import os
from urllib.parse import urlparse

# Parse DATABASE_URL for Heroku
database_url = os.getenv('DATABASE_URL')
if database_url:
    result = urlparse(database_url)
    DB_CONFIG = {
        'dbname': result.path[1:],
        'user': result.username,
        'password': result.password,
        'host': result.hostname,
        'port': result.port or 5432
    }
else:
    # Fallback for local development
    DB_CONFIG = {
        'dbname': os.getenv('DB_NAME', 'sports_odds'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgrespass12312312312312'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }
