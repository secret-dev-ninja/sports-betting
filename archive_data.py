import psycopg2
import logging
from config import DB_CONFIG
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os
from utils import get_uname
from typing import Dict

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

class CacheManager:
    def __init__(self):
        self.cache = {}
    
    def has_changed(self, table: str, key: tuple, new_value: Dict) -> bool:
        """
        Check if the value has changed from the cached version
        """
        cache_key = (table,) + key
        if cache_key not in self.cache:
            self.cache[cache_key] = new_value
            return True
        
        if self.cache[cache_key] != new_value:
            self.cache[cache_key] = new_value
            return True
            
        return False

class ArchiveManager:
    def archive_recent_data(self, minutes_old=10):
        """Move data older than specified minutes to archive database."""
        try:
            cache_manager = CacheManager()

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
                    
                    # events
                    source_cur.execute("""
                        SELECT event_id, sport_id, sport_uname, league_id, league_name, league_uname, starts, home_team, home_team_uname,
                        away_team, away_team_uname, event_type, parent_id, resulting_unit, is_have_odds, event_category 
                        FROM events WHERE event_id = %s
                    """, (event_id,))
                    events = source_cur.fetchall()

                    if events:
                        for event in events:
                            archive_cur.execute('''
                            INSERT INTO events (
                                event_id, sport_id, sport_uname, league_id, league_name, league_uname, starts, home_team, home_team_uname,
                                away_team, away_team_uname, event_type, parent_id, resulting_unit, is_have_odds, event_category
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (event_id) DO UPDATE SET
                                archived_at = CURRENT_TIMESTAMP
                            ''', (
                                event[0], event[1], get_uname(event[2]), event[3],
                                event[4], get_uname(event[5]), event[6], event[7],
                                get_uname(event[8]), event[9], get_uname(event[10]), event[11],
                                event[12], event[13], event[14], event[15]
                            ))

                            source_cur.execute("""
                                SELECT event_id, period_number, period_status, cutoff, max_spread, max_money_line, max_total, max_team_total 
                                FROM periods WHERE event_id = %s
                            """, (event_id,))
                            periods = source_cur.fetchall()

                            if periods:
                                for period in periods:
                                    archive_cur.execute('''
                                    INSERT INTO periods (
                                        event_id, period_number, period_status, cutoff, max_spread, max_money_line, max_total, max_team_total
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (event_id, period_number) DO UPDATE SET
                                        archived_at = CURRENT_TIMESTAMP
                                    ''', (
                                        period[0], period[1], period[2], period[3], 
                                        period[4], period[5], period[6], period[7]
                                    ))

                                    source_cur.execute("""
                                        SELECT period_id, home_odds, draw_odds, away_odds, max_bet 
                                        FROM money_lines WHERE period_id = %s
                                    """, (period[0],))
                                    money_lines = source_cur.fetchall()

                                    if money_lines:
                                        for money_line in money_lines:
                                            data = {
                                                'home': money_line[1],
                                                'draw': money_line[2],
                                                'away': money_line[3],
                                                'max': money_line[4]
                                            }

                                            if cache_manager.has_changed('money_lines', (money_line[0],), data):
                                                archive_cur.execute('''
                                                INSERT INTO money_lines (
                                                    period_id, home_odds, draw_odds, away_odds, max_bet
                                                ) VALUES (%s, %s, %s, %s, %s)
                                                ''', (
                                                    money_line[0], money_line[1], money_line[2], 
                                                    money_line[3], money_line[4]
                                                ))

                                    source_cur.execute("""
                                        SELECT period_id, handicap, alt_line_id, home_odds, away_odds, max_bet 
                                        FROM spreads WHERE period_id = %s
                                    """, (period[0],))
                                    spreads = source_cur.fetchall()

                                    if spreads:
                                        for spread in spreads:
                                            data = {
                                                'hdp': spread[1],
                                                'home': spread[2],
                                                'draw': spread[3],
                                                'away': spread[4],
                                                'max': spread[5]
                                            }

                                            if cache_manager.has_changed('spreads', (spread[0],), data):
                                                archive_cur.execute('''
                                                INSERT INTO spreads (
                                                    period_id, handicap, alt_line_id, home_odds, away_odds, max_bet
                                                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                                ''', (
                                                    spread[0], spread[1], spread[2], spread[3], spread[4], spread[5]
                                                ))

                                    source_cur.execute("""
                                        SELECT period_id, time, points, alt_line_id, over_odds, under_odds, max_bet 
                                        FROM totals WHERE period_id = %s
                                    """, (period[0],))
                                    totals = source_cur.fetchall()

                                    if totals:
                                        for total in totals:
                                            data = {
                                                'points': total[2],
                                                'over': total[3],
                                                'under': total[4],
                                                'max': total[5]
                                            }

                                            if cache_manager.has_changed('totals', (total[0],), data):
                                                archive_cur.execute('''
                                                INSERT INTO totals (
                                                    time, period_id, points, alt_line_id, over_odds, under_odds, max_bet
                                                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                                ''', (
                                                    total[0], total[1], total[2], total[3], total[4], total[5], total[6]
                                                ))
                                            
                    # Copy data to archive
                    tables = ['events', 'periods', 'money_lines', 'spreads', 'totals', 'team_totals']

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