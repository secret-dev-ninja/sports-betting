import psycopg2
import logging
from config import DB_CONFIG
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Set up logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('archive_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('archive_manager')

class ArchiveManager:
    def archive_recent_data(self, minutes_old=10):
        """Move data older than specified minutes to archive database."""
        try:
            # Connect to both databases
            source_conn = psycopg2.connect(**DB_CONFIG)
            archive_params = DB_CONFIG.copy()
            archive_params['dbname'] = f"{DB_CONFIG['dbname']}_archive"
            archive_conn = psycopg2.connect(**archive_params)
            
            source_cur = source_conn.cursor()
            archive_cur = archive_conn.cursor()

            # Archive events and related data
            cutoff_time = datetime.now() - timedelta(minutes=minutes_old)
            source_cur.execute("""
                SELECT event_id FROM events 
                WHERE starts < %s AT TIME ZONE 'UTC'
                AND event_id NOT IN (
                    SELECT event_id FROM events 
                    WHERE starts >= %s AT TIME ZONE 'UTC'
                )
            """, (cutoff_time, cutoff_time))
            
            old_event_ids = [row[0] for row in source_cur.fetchall()]

            if not old_event_ids:
                logger.info("No new data to archive")
                return

            archived_count = 0
            for event_id in old_event_ids:
                try:
                    # Begin transaction for this event
                    source_cur.execute("BEGIN")
                    archive_cur.execute("BEGIN")

                    # Copy data to archive
                    tables = ['events', 'periods', 'money_lines', 'spreads', 'totals', 'team_totals']
                    
                    for table in tables:
                        if table == 'events':
                            source_cur.execute(f"SELECT * FROM {table} WHERE event_id = %s", (event_id,))
                        elif table == 'periods':
                            source_cur.execute(f"SELECT * FROM {table} WHERE event_id = %s", (event_id,))
                        else:
                            source_cur.execute(f"""
                                SELECT t.* FROM {table} t
                                JOIN periods p ON p.period_id = t.period_id
                                WHERE p.event_id = %s
                            """, (event_id,))
                        
                        rows = source_cur.fetchall()
                        
                        if rows:
                            columns = [desc[0] for desc in source_cur.description]
                            # Add archived_at column
                            columns.append('archived_at')
                            values_str = ','.join(['%s'] * len(columns))
                            insert_query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({values_str})"
                            if table == 'events':
                                insert_query = insert_query + " ON CONFLICT (event_id) DO UPDATE SET archived_at = CURRENT_TIMESTAMP"
                            # Add current timestamp to each row
                            current_time = datetime.now()
                            modified_rows = [row + (current_time,) for row in rows]

                            archive_cur.executemany(insert_query, modified_rows)

                    # Delete data from source
                    for table in reversed(tables):  # Delete in reverse order due to foreign keys
                        if table == 'events':
                            source_cur.execute(f"DELETE FROM {table} WHERE event_id = %s", (event_id,))
                        elif table == 'periods':
                            source_cur.execute(f"DELETE FROM {table} WHERE event_id = %s", (event_id,))
                        else:
                            source_cur.execute(f"""
                                DELETE FROM {table} 
                                WHERE period_id IN (
                                    SELECT period_id FROM periods WHERE event_id = %s
                                )
                            """, (event_id,))

                    # Commit transaction for this event
                    source_cur.execute("COMMIT")
                    archive_cur.execute("COMMIT")
                    archived_count += 1
                    logger.info(f"Successfully archived event_id: {event_id}")

                except Exception as e:
                    # Rollback transaction for this event if there's an error
                    source_cur.execute("ROLLBACK")
                    archive_cur.execute("ROLLBACK")
                    logger.error(f"Error archiving event_id {event_id}: {e}")
                    continue

            logger.info(f"Archive run completed. Successfully archived {archived_count} out of {len(old_event_ids)} events")

        except Exception as e:
            logger.error(f"Error in archive process: {e}")
            raise
        finally:
            source_cur.close()
            archive_cur.close()
            source_conn.close()
            archive_conn.close()

def run_archive_job():
    """Main function to run the archive job continuously."""
    archive_manager = ArchiveManager()
    
    while True:
        try:
            start_time = time.time()
            logger.info("Starting archive job...")
            
            archive_manager.archive_recent_data(minutes_old=int(os.getenv('ARCHIVE_INTERVAL')))
            
            # Calculate sleep time to maintain 10-minute intervals
            execution_time = time.time() - start_time
            sleep_time = max(0, 60 * int(os.getenv('ARCHIVE_INTERVAL')) - execution_time)  # 600 seconds = 10 minutes
            
            logger.info(f"Archive job completed. Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error in archive job: {e}")
            time.sleep(60)  # Wait 1 minute before retrying if there's an error

if __name__ == "__main__":
    run_archive_job()