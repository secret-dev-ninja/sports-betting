from create_database import DatabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    db = DatabaseManager()
    try:
        db.ensure_database_exists()
        db.ensure_tables_exist()
        db.verify_tables()
    except Exception as e:
        logging.error(f"Error: {e}")