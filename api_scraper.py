import psycopg2
import psycopg2.extras
import requests
from datetime import datetime
import json
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
from config import DB_CONFIG
import multiprocessing

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('odds_collector.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('odds_collector')

class DatabaseManager:
    def __init__(self):
        self.conn_params = DB_CONFIG
        self.cache = {}
        self.first_pass = True
        self.changes_this_update = set()

    def get_connection(self):
        """Create and return a database connection"""
        return psycopg2.connect(**self.conn_params)

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

    def clear_changes(self):
        """Clear the changes set at the start of each update"""
        self.changes_this_update.clear()

    def verify_data_counts(self, conn):
        """Verify the counts of data in each table"""
        cur = conn.cursor()
        try:
            verification_queries = {
                'events': "SELECT COUNT(*) FROM events",
                'periods': "SELECT COUNT(*) FROM periods",
                'money_lines': "SELECT COUNT(*) FROM money_lines",
                'spreads': "SELECT COUNT(*) FROM spreads",
                'totals': "SELECT COUNT(*) FROM totals",
                'team_totals': "SELECT COUNT(*) FROM team_totals"
            }
            
            for table, query in verification_queries.items():
                cur.execute(query)
                count = cur.fetchone()[0]
                logger.info(f"Count in {table}: {count}")
                
        except Exception as e:
            logger.error(f"Error verifying data: {e}")
        finally:
            cur.close()

    def insert_log(self, conn, sports, last):
        cur = conn.cursor()
        # Check if the log already exists
        cur.execute('''
            SELECT 1 FROM api_request_logs 
            WHERE sport_id = %s AND last_call = %s
        ''', (sports, last))

        # If no rows are returned, insert the new log
        if cur.fetchone() is None:
            try:
                # Execute the INSERT query
                cur.execute('''
                    INSERT INTO api_request_logs (
                        sport_id, last_call, created_at
                    ) VALUES (%s, %s, DEFAULT)
                ''', (sports, last))

                # Commit the transaction
                conn.commit()
                print("Request log inserted successfully.")
            except psycopg2.Error as e:
                # Rollback in case of an error
                conn.rollback()
                print(f"An error occurred: {e}")
        else:
            print("Request log already exists. No insert performed.")

    def get_last_call(self, conn, sports):
        cur = conn.cursor()
        try:
            query = '''
                SELECT MAX(last_call) FROM api_request_logs 
                WHERE sport_id = %s;
            '''
            cur.execute(query, (sports,))
            return cur.fetchone()[0]
            
        except Exception as e:
            logger.error(f"Error inserting log: {e}")

class OddsCollector:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.last_timestamp = None

    def get_pinnacle_odds(self, sport_id: str) -> Optional[Dict]:
        conn = self.db_manager.get_connection()

        if not self.last_timestamp:
            last = self.db_manager.get_last_call(conn, sport_id)
            if last:
                self.last_timestamp = last

        """Fetch odds data from Pinnacle API"""
        url = os.getenv('PINNACLE_API_URL', "https://pinnacle-odds.p.rapidapi.com/kit/v1/markets")
        
        headers = {
            "x-rapidapi-host": os.getenv('PINNACLE_API_HOST', "pinnacle-odds.p.rapidapi.com"),
            "x-rapidapi-key": os.getenv('PINNACLE_API_KEY', 'a8566af92cmsha8a9ac59b2a9cbcp11230fjsn67dc35effb7f')
        }
        
        params = {
            "sport_id": sport_id,
            "is_have_odds": "true"
        }
        
        if self.last_timestamp:
            params["since"] = str(self.last_timestamp)
        
        logger.info(f"Making API request to Pinnacle{' with sport_id=' + str(sport_id) + ' since=' + str(self.last_timestamp) if self.last_timestamp else ''}")
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'last' in data:
                self.last_timestamp = data['last']
                logger.info('set last_timestamp:' + str(self.last_timestamp))
            
            self.db_manager.insert_log(conn, sport_id, self.last_timestamp)

            return data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None

    def store_event(self, conn, event: Dict[str, Any], cur=None) -> None:
        """Store event and its related data in the database"""
        if cur is None:
            cur = conn.cursor()
        
        try:
            # Determine event category
            event_category = 'standard'
            if event.get('resulting_unit') in ['Corners', 'Bookings']:
                event_category = event['resulting_unit'].lower()
                
            data_changed = False
            changed_items = {
                'money_line': False,
                'spreads': set(),
                'totals': set(),
                'team_totals': set()
            }
            
            # Track changes for all event types
            for period_key, period in event['periods'].items():
                # Money line tracking
                if period.get('money_line'):
                    money_line_data = {
                        'home_odds': period['money_line'].get('home'),
                        'draw_odds': period['money_line'].get('draw'),
                        'away_odds': period['money_line'].get('away')
                    }
                    if self.db_manager.has_changed('money_lines', (event['event_id'], period_key), money_line_data):
                        data_changed = True
                        changed_items['money_line'] = True

                # Spreads tracking
                if period.get('spreads'):
                    for handicap_key, spread in period['spreads'].items():
                        handicap = float(spread.get('hdp', handicap_key))  # Support both hdp and direct handicap
                        spread_data = {
                            'home_odds': spread.get('home'),
                            'away_odds': spread.get('away'),
                            'max_bet': spread.get('max')
                        }
                        if self.db_manager.has_changed('spreads', (event['event_id'], period_key, handicap), spread_data):
                            data_changed = True
                            changed_items['spreads'].add(handicap)

                # Totals tracking
                if period.get('totals'):
                    for points, total in period['totals'].items():
                        total_data = {
                            'over_odds': total.get('over'),
                            'under_odds': total.get('under'),
                            'max_bet': total.get('max')
                        }
                        if self.db_manager.has_changed('totals', (event['event_id'], period_key, float(points)), total_data):
                            data_changed = True
                            changed_items['totals'].add(float(points))

                # Team totals tracking
                if period.get('team_total'):
                    for team_type, team_data in period['team_total'].items():
                        if team_data:
                            team_total_data = {
                                'points': team_data.get('points'),
                                'over_odds': team_data.get('over'),
                                'under_odds': team_data.get('under')
                            }
                            if self.db_manager.has_changed('team_totals', (event['event_id'], period_key, team_type), team_total_data):
                                data_changed = True
                                changed_items['team_totals'].add(team_type)

            # Log changes if detected
            if data_changed and not self.db_manager.first_pass:
                self.db_manager.changes_this_update.add(f"{event['home']} vs {event['away']}")
                
                changes_desc = []
                if changed_items['money_line']:
                    changes_desc.append("Moneyline")
                if changed_items['spreads']:
                    changes_desc.append(f"Spreads (handicaps: {sorted(changed_items['spreads'])})")
                if changed_items['totals']:
                    changes_desc.append(f"Totals (points: {sorted(changed_items['totals'])})")
                if changed_items['team_totals']:
                    changes_desc.append(f"Team Totals ({', '.join(changed_items['team_totals'])})")
                logger.info(f"Changes detected for {event['home']} vs {event['away']}: {', '.join(changes_desc)}")

            # Insert or update event
            cur.execute('''
            INSERT INTO events (
                event_id, sport_id, league_id, league_name, starts, home_team, 
                away_team, event_type, parent_id, resulting_unit, is_have_odds, event_category
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE SET
                last_updated = CURRENT_TIMESTAMP,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team
            ''', (
                event['event_id'], event['sport_id'], event['league_id'],
                event['league_name'], event['starts'], event['home'],
                event['away'], event['event_type'], event['parent_id'],
                event['resulting_unit'], event['is_have_odds'], event_category
            ))
            
            # Process periods
            for period_key, period in event['periods'].items():
                period_number = int(period_key.replace('num_', ''))
                
                cur.execute('''
                    INSERT INTO periods (
                        event_id, period_number, period_status, cutoff,
                        max_spread, max_money_line, max_total, max_team_total,
                        line_id, number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id, period_number)
                    DO UPDATE SET 
                        period_status = EXCLUDED.period_status,
                        cutoff = EXCLUDED.cutoff,
                        max_spread = EXCLUDED.max_spread,
                        max_money_line = EXCLUDED.max_money_line,
                        max_total = EXCLUDED.max_total,
                        max_team_total = EXCLUDED.max_team_total,
                        line_id = EXCLUDED.line_id,
                        number = EXCLUDED.number
                    RETURNING period_id
                ''', (
                    event['event_id'],
                    period_number,
                    period['period_status'],
                    period['cutoff'],
                    period['meta'].get('max_spread'),
                    period['meta'].get('max_money_line'),
                    period['meta'].get('max_total'),
                    period['meta'].get('max_team_total'),
                    period.get('line_id'),
                    period.get('number')
                ))
                
                period_id = cur.fetchone()[0]
                current_time = datetime.now()

                # Only insert new rows for changed odds
                if changed_items['money_line'] and period.get('money_line'):
                    cur.execute('''
                    INSERT INTO money_lines (
                        time, period_id, home_odds, draw_odds, away_odds, max_bet
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        current_time,
                        period_id,
                        period['money_line'].get('home'),
                        period['money_line'].get('draw'),
                        period['money_line'].get('away'),
                        period['meta'].get('max_money_line')
                    ))

                if period.get('spreads'):
                    for handicap_key, spread in period['spreads'].items():
                        handicap = float(spread.get('hdp', handicap_key))
                        if handicap in changed_items['spreads']:
                            cur.execute('''
                            INSERT INTO spreads (
                                time, period_id, handicap, alt_line_id,
                                home_odds, away_odds, max_bet
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                current_time,
                                period_id,
                                handicap,
                                spread.get('alt_line_id'),
                                spread.get('home'),
                                spread.get('away'),
                                spread.get('max')
                            ))

                if period.get('totals'):
                    for points, total in period['totals'].items():
                        if float(points) in changed_items['totals']:
                            cur.execute('''
                            INSERT INTO totals (
                                time, period_id, points, alt_line_id,
                                over_odds, under_odds, max_bet
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                current_time,
                                period_id,
                                float(points),
                                total.get('alt_line_id'),
                                total.get('over'),
                                total.get('under'),
                                total.get('max')
                            ))

                if period.get('team_total'):
                    for team_type, team_data in period['team_total'].items():
                        if team_data and team_type in changed_items['team_totals']:
                            cur.execute('''
                            INSERT INTO team_totals (
                                time, period_id, team_type, points,
                                over_odds, under_odds, max_bet
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                current_time,
                                period_id,
                                team_type,
                                team_data.get('points'),
                                team_data.get('over'),
                                team_data.get('under'),
                                period['meta'].get('max_team_total')
                            ))

            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing event {event['event_id']}: {str(e)}")
            raise

def get_sports_ids():
    url = os.getenv('PINNACLE_API_SPORTS_URL', "https://pinnacle-odds.p.rapidapi.com/kit/v1/sports")
        
    headers = {
        "x-rapidapi-host": os.getenv('PINNACLE_API_HOST', "pinnacle-odds.p.rapidapi.com"),
        "x-rapidapi-key": os.getenv('PINNACLE_API_KEY', 'a8566af92cmsha8a9ac59b2a9cbcp11230fjsn67dc35effb7f')
    }

    logger.info("Requesting sports list information from Pinnacle API")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        ids = [sport['id'] for sport in data]
        return ids
        
    except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None

def store_sport_info(collector, sport_id):
    while True:
        try:
            collector.db_manager.clear_changes()
            data = collector.get_pinnacle_odds(sport_id)
            
            if not data or not data.get('events'):
                logger.info("No new data received from API")
                time.sleep(1)
                continue
            
            conn = collector.db_manager.get_connection()
            cur = conn.cursor()
            
            try:
                for event in data['events']:
                    try:
                        collector.store_event(conn, event, cur)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        continue

                if collector.db_manager.first_pass:
                    logger.info("Initial data load complete")
                    # collector.db_manager.verify_data_counts(conn)
                    collector.db_manager.first_pass = False
                elif collector.db_manager.changes_this_update:
                    logger.info("Updates detected for:")
                    for game in sorted(collector.db_manager.changes_this_update):
                        logger.info(f"  • {game}")
            except Exception as e:
                logger.error(f"Process failed: {e}")

            finally:
                cur.close()
                conn.close()
            
        except Exception as e:
            logger.error(f"Process failed: {e}")
        
        time.sleep(1)

RATE_LIMIT = 5
DELAY = 1 / RATE_LIMIT 
MAX_CONCURRENT_REQUESTS = 3

semaphore = multiprocessing.Semaphore(MAX_CONCURRENT_REQUESTS)

def process_sport_id(collector, sport_id):
    with semaphore:
        store_sport_info(collector, sport_id)


def main():
    logger.info("Starting odds collection process")
    collector = OddsCollector()
    sport_ids = get_sports_ids()

    with multiprocessing.Pool() as pool:
        pool.starmap(process_sport_id, [(collector, sport_id) for sport_id in sport_ids])
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise