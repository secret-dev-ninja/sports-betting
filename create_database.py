import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from config import DB_CONFIG
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('database_manager')

class DatabaseManager:
    def ensure_database_exists(self):
        """Ensure the database exists and create it if not."""
        try:
            # Connect to the default 'postgres' database
            default_params = DB_CONFIG.copy()
            default_params['dbname'] = 'postgres'
            conn = psycopg2.connect(**default_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Check if the database already exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['dbname'],))
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")
                logger.info(f"Database {DB_CONFIG['dbname']} created successfully.")
            else:
                logger.info(f"Database {DB_CONFIG['dbname']} already exists.")

            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error ensuring database exists: {e}")
            raise

    def ensure_tables_exist(self):
        """Create necessary tables if they don't exist."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Create TimescaleDB extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            logger.info("TimescaleDB extension ensured.")

            # # Create tables

            cur.execute('''
            CREATE TABLE IF NOT EXISTS api_request_logs (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                event_id BIGINT,
                since TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id BIGINT PRIMARY KEY,
                sport_id INTEGER,
                league_id INTEGER,
                league_name TEXT,
                starts TIMESTAMPTZ,
                home_team TEXT,
                away_team TEXT,
                event_type TEXT,
                parent_id BIGINT,
                resulting_unit TEXT,
                is_have_odds BOOLEAN,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                event_category TEXT
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS periods (
                period_id BIGSERIAL PRIMARY KEY,
                event_id BIGINT,
                period_number INTEGER,
                period_status INTEGER,
                cutoff TIMESTAMPTZ,
                max_spread DECIMAL,
                max_money_line DECIMAL,
                max_total DECIMAL,
                max_team_total DECIMAL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                line_id BIGINT,
                number INTEGER,
                FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
                CONSTRAINT unique_event_period UNIQUE (event_id, period_number)
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS money_lines (
                time TIMESTAMPTZ NOT NULL,
                period_id BIGINT,
                home_odds DECIMAL,
                draw_odds DECIMAL,
                away_odds DECIMAL,
                max_bet DECIMAL,
                FOREIGN KEY (period_id) REFERENCES periods (period_id) ON DELETE CASCADE
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS spreads (
                time TIMESTAMPTZ NOT NULL,
                period_id BIGINT,
                handicap DECIMAL,
                alt_line_id BIGINT,
                home_odds DECIMAL,
                away_odds DECIMAL,
                max_bet DECIMAL,
                FOREIGN KEY (period_id) REFERENCES periods (period_id) ON DELETE CASCADE
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS totals (
                time TIMESTAMPTZ NOT NULL,
                period_id BIGINT,
                points DECIMAL,
                alt_line_id BIGINT,
                over_odds DECIMAL,
                under_odds DECIMAL,
                max_bet DECIMAL,
                FOREIGN KEY (period_id) REFERENCES periods (period_id) ON DELETE CASCADE
            );
            ''')

            cur.execute('''
            CREATE TABLE IF NOT EXISTS team_totals (
                time TIMESTAMPTZ NOT NULL,
                period_id BIGINT,
                team_type TEXT,
                points DECIMAL,
                over_odds DECIMAL,
                under_odds DECIMAL,
                max_bet DECIMAL,
                FOREIGN KEY (period_id) REFERENCES periods (period_id) ON DELETE CASCADE
            );
            ''')

            # Convert tables to hypertables
            for table in ['money_lines', 'spreads', 'totals', 'team_totals']:
                cur.execute(f"SELECT create_hypertable('{table}', 'time', if_not_exists => TRUE);")

            # Commit changes and close
            conn.commit()
            logger.info("All tables created or verified successfully.")
            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def verify_tables(self):
        """Verify if the necessary tables exist."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Check if the expected tables exist
            expected_tables = ['events', 'periods', 'money_lines', 'spreads', 'totals', 'team_totals']
            for table in expected_tables:
                cur.execute(f"SELECT to_regclass('{table}');")
                result = cur.fetchone()
                if result[0] is None:
                    logger.warning(f"Table {table} does not exist.")
                else:
                    logger.info(f"Table {table} exists.")

            # Close connection
            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error verifying tables: {e}")
            raise

    def setup_triggers(self):
        logger.info("Setting up triggers in the database.")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Create notification function
            cur.execute("""
            CREATE OR REPLACE FUNCTION notify_odds_update() RETURNS TRIGGER AS $$
            BEGIN
                -- For events table
                IF TG_TABLE_NAME = 'events' THEN
                    PERFORM pg_notify('odds_update', json_build_object(
                        'sport_id', NEW.sport_id,
                        'event_id', NEW.event_id,
                        'home_team', NEW.home_team,
                        'away_team', NEW.away_team,
                        'table_updated', TG_TABLE_NAME,
                        'update_time', CURRENT_TIMESTAMP
                    )::text);
                -- For other odds tables
                ELSE 
                    PERFORM pg_notify('odds_update', json_build_object(
                        'sport_id', e.sport_id,
                        'event_id', e.event_id,
                        'home_team', e.home_team,
                        'away_team', e.away_team,
                        'table_updated', TG_TABLE_NAME,
                        'update_time', CURRENT_TIMESTAMP
                    )::text)
                    FROM periods p
                    JOIN events e ON e.event_id = p.event_id
                    WHERE p.period_id = NEW.period_id;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """)

            # Create triggers for relevant tables
            triggers = ["events", "money_lines", "spreads", "totals", "team_totals"]
            for table in triggers:
                cur.execute(f"""
                DROP TRIGGER IF EXISTS odds_notify_trigger ON {table};
                CREATE TRIGGER odds_notify_trigger
                    AFTER INSERT ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION notify_odds_update();
                """)
            
            conn.commit()
            logger.info("Configured triggers successfully.")
            cur.close()
            conn.close()

        except Exception as e:
            conn.rollback()
            logger.error(f"Error Configuring triggers: {e}")
            raise

if __name__ == "__main__":
    db = DatabaseManager()
    db.ensure_database_exists()
    db.ensure_tables_exist()
    db.setup_triggers()

