from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import json
import asyncio
import logging
from typing import List
from dotenv import load_dotenv
from config import DB_CONFIG
import requests
import os
from utils import get_uname, get_sum_vig, calculate_vig_free_odds, get_no_vig_odds_multiway

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_backend")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connection established.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket connection closed.")
        else:
            logger.warning("WebSocket was not found in active connections.")

manager = ConnectionManager()

def get_db_connection(type: str = 'live'):
    try:
        if type == 'live':
            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        else:
            params = DB_CONFIG.copy()
            params['dbname'] = f"{DB_CONFIG['dbname']}_archive"
            conn = psycopg2.connect(**params)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/receive-event")
async def receive_event(event_id: str, type: str = 'live'):
    try:
        # Add the received event_id to the storage
        conn = get_db_connection(type=type)
        cursor = conn.cursor()

        # Query to get period_ids by event_id
        cursor.execute("""
            SELECT period_id
            FROM periods
            WHERE event_id = %s ORDER BY period_number ASC;
        """, (event_id,))

        periods = cursor.fetchall()

        # If no periods are found for the given event_id
        if not periods:
            raise HTTPException(status_code=404, detail="No periods found for the provided event_id")
        
        result = []
        for period in periods:
            # Query to get the money_line data for a specific period_id
            base_query = """
                SELECT
                    ml.home_odds,
                    ml.draw_odds,
                    ml.away_odds,
                    ml.max_bet,
                    ml.time AT TIME ZONE 'UTC' AS time
                FROM
                    money_lines ml
                JOIN periods p ON ml.period_id = p.period_id
                WHERE
                    p.period_id = %s
            """
            time_condition = "AND p.cutoff >= ml.time AT TIME ZONE 'UTC'" if type == 'live' else ''
            complete_query = base_query + time_condition + """
                ORDER BY ml.time DESC LIMIT 1
            """

            cursor.execute(complete_query, (period))
            money_lines = cursor.fetchall()
            money_line_results = [
                {
                    'home': money_line[0],
                    'home_vf': get_no_vig_odds_multiway([money_line[0], money_line[1], money_line[2]])[0],
                    'draw': money_line[1],
                    'away': money_line[2],
                    'away_vf': get_no_vig_odds_multiway([money_line[0], money_line[1], money_line[2]])[2],
                    'max_bet': money_line[3],
                    'vig': get_sum_vig('moneyline', [
                        money_line[0],
                        money_line[1],
                        money_line[2]
                    ]),
                    'time': money_line[4]
                } for money_line in money_lines
            ]

            # Query to get the spread data for a specific period_id
            base_query = """
                SELECT DISTINCT ON ( handicap ) s.handicap,
                    s.home_odds,
                    s.away_odds,
                    s.max_bet,
                    s.time AT TIME ZONE 'UTC' AS time 
                FROM
                    spreads s
                JOIN periods P ON s.period_id = P.period_id 
                WHERE
                    s.period_id = %s 
            """
            time_condition = "AND p.cutoff >= s.time AT TIME ZONE 'UTC'" if type == 'live' else ''
            complete_query = base_query + time_condition + """
                ORDER BY s.handicap, s.time DESC;
            """

            cursor.execute(complete_query, (period,))
            spreads = cursor.fetchall()
            spread_results = [
                {
                    "handicap": spread[0],
                    "home_odds": spread[1],
                    "home_vf": str(calculate_vig_free_odds(spread[1], spread[2])[0]),
                    "away_odds": spread[2],
                    "away_vf": str(calculate_vig_free_odds(spread[1], spread[2])[1]),
                    "max_bet": spread[3],
                    "vig": get_sum_vig('spread', [spread[1], spread[2]]),
                    "time": spread[4]
                } for spread in spreads
            ]

            # Query to get the total data for a specific period_id
            base_query = """
                SELECT 
                    DISTINCT ON (points)
                    t.points, 
                    t.over_odds, 
                    t.under_odds, 
                    t.max_bet,
                    t.time AT TIME ZONE 'UTC' AS time
                FROM 
                    totals t
                JOIN periods p ON t.period_id = p.period_id
                WHERE 
                    t.period_id = %s
            """
            time_condition = "AND p.cutoff >= t.time AT TIME ZONE 'UTC'" if type == 'live' else ''
            complete_query = base_query + time_condition + """
                ORDER BY t.points, t.time DESC;
            """

            cursor.execute(complete_query, (period,))
            totals = cursor.fetchall()
            total_results = [
                {
                    "points": total[0],
                    "over_odds": total[1],
                    "over_vf": str(calculate_vig_free_odds(total[1], total[2])[0]),
                    "under_odds": total[2],
                    "under_vf": str(calculate_vig_free_odds(total[1], total[2])[1]),
                    "max_bet": total[3],
                    "vig": get_sum_vig('total', [total[1], total[2]]),
                    "time": total[4]
                } for total in totals
            ]

            # Append the result as a dictionary
            result.append({
                "period_id": period,
                "money_line": money_line_results,
                "spread": spread_results,
                "total": total_results
            })

        return {"message": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in /receive-event: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        
@app.get("/receive-chart-event")
async def receive_chart_event(period_id: str, hdp: float = None, points: float = None, table: str = None, type: str = 'live'):
    if table == 'spread':
        try: 
            # Add the received event_id to the storage
            conn = get_db_connection(type=type)
            cursor = conn.cursor()

            # Query to get period_ids by event_id
            base_query = """
                SELECT
                    * 
                FROM
                    ( SELECT s.home_odds, s.away_odds, s.time AT TIME ZONE 'UTC' AS time, s.max_bet
                    FROM spreads s
                    JOIN periods p ON s.period_id = p.period_id
                    WHERE s.period_id = %s AND s.handicap = %s
            """
            time_condition = "AND p.cutoff >= s.time AT TIME ZONE 'UTC'" if type == 'live' else ''

            complete_query = base_query + time_condition + """
                    ORDER BY s.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """
            cursor.execute(complete_query, (period_id, hdp))

            spreads = cursor.fetchall()
            result = [{
                'time': spread[2].strftime('%m-%d %H:%M'),
                'home': spread[0], 
                'away': spread[1],
                'limit': spread[3]
            } for spread in spreads]
            
            return {"message": "success", "data": result}
        except Exception as e:
            logger.error(f"Error in /receive-chart-event: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while fetching chart data")
    elif table == 'money_line':
        try: 
            # Add the received event_id to the storage
            conn = get_db_connection(type=type)
            cursor = conn.cursor()

            # Query to get period_ids by event_id
            base_query = """
                SELECT
                    * 
                FROM
                    ( SELECT ml.home_odds, ml.away_odds, ml.time AT TIME ZONE 'UTC' AS time, ml.max_bet
                    FROM money_lines ml
                    JOIN periods p ON ml.period_id = p.period_id
                    WHERE ml.period_id = %s
            """
            time_condition = "AND p.cutoff >= ml.time AT TIME ZONE 'UTC'" if type == 'live' else ''

            complete_query = base_query + time_condition + """
                    ORDER BY ml.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """

            cursor.execute(complete_query, (period_id,))

            spreads = cursor.fetchall()
            result = [{
                'time': spread[2].strftime('%m-%d %H:%M'),
                'home': spread[0], 
                'away': spread[1],
                'limit': spread[3]
            } for spread in spreads]
            
            return {"message": "success", "data": result}
        except Exception as e:
            logger.error(f"Error in /receive-chart-event: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while fetching chart data")
    elif table == 'total':
        try:
            conn = get_db_connection(type=type)
            cursor = conn.cursor()

            base_query = """
                SELECT
                    * 
                FROM
                    ( SELECT t.over_odds, t.under_odds, t.time AT TIME ZONE 'UTC' AS time, t.max_bet
                    FROM totals t
                    JOIN periods p ON t.period_id = p.period_id
                    WHERE t.period_id = %s and t.points = %s
            """
            time_condition = "AND p.cutoff >= t.time AT TIME ZONE 'UTC'" if type == 'live' else ''

            complete_query = base_query + time_condition + """
                    ORDER BY t.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """

            cursor.execute(complete_query, (period_id, points))

            totals = cursor.fetchall()
            result = [{
                'over': total[0], 
                'under': total[1],
                'time': total[2].strftime('%m-%d %H:%M'),
                'limit': total[3]
            } for total in totals]

            return {"message": "success", "data": result}
        except Exception as e:
            logger.error(f"Error in /receive-chart-event: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while fetching chart data")

@app.get("/receive-options-event")
async def receive_options_event(sport_name: str = None, league_name: str = None, type: str = 'live'):
    if sport_name is None and league_name is None:
        url = os.getenv('PINNACLE_API_SPORTS_URL')
        
        headers = {
            "x-rapidapi-host": os.getenv('PINNACLE_API_HOST'),
            "x-rapidapi-key": os.getenv('PINNACLE_API_KEY')
        }

        logger.info("Requesting sports list information from Pinnacle API")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            sports =  [{"value": get_uname(sport['name']), "label": sport['name']} for sport in data]
            return sports   
            
        except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                return None
    elif sport_name is not None and league_name is None:
        conn = get_db_connection(type=type)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT league_uname, league_name
            FROM events
            WHERE sport_uname = %s ORDER BY league_name ASC;
        """, (sport_name,))

        leagues = cursor.fetchall()
        leaguesOpts = [{
            'value': league[0],
            'label': league[1], 
        } for league in leagues]

        cursor.execute("""
        SELECT DISTINCT team_name, team
        FROM (
            SELECT home_team_uname AS team_name, home_team AS team
            FROM events
            WHERE sport_uname = %s
            UNION ALL
            SELECT away_team_uname AS team_name, away_team AS team
            FROM events
            WHERE sport_uname = %s
        ) AS combined_teams ORDER BY team ASC;
        """, (sport_name, sport_name))
    
        teams = cursor.fetchall()
        teamsOpts = [{
            'value': team[0],
            'label': team[1],
        } for team in teams]

        return {
            'leagues': leaguesOpts,
            'teams': teamsOpts
        }
    elif sport_name is not None and league_name is not None:
        conn = get_db_connection(type=type)
        cursor = conn.cursor()

        logger.info('starting receive-options...%s, %s', sport_name, league_name)

        cursor.execute("""
        SELECT DISTINCT team_name, team
        FROM (
            SELECT home_team_uname AS team_name, home_team AS team
            FROM events
            WHERE sport_uname = %s
            AND league_uname = %s
            UNION ALL
            SELECT away_team_uname AS team_name, away_team AS team
            FROM events
            WHERE sport_uname = %s
            AND league_uname = %s
        ) AS combined_teams ORDER BY team ASC;
        """, (sport_name, league_name, sport_name, league_name))

        teams = cursor.fetchall()
        result = [{
            'value': team[0],
            'label': team[1],
        } for team in teams]

        return result

@app.get("/receive-event-info")
async def receive_event_info(sport_name: str, league_name: str = '', team_name: str = '', type: str = 'live'):
    conn = get_db_connection(type=type)
    cursor = conn.cursor()

    if league_name != '' and team_name == '':
        query = ""
        if type == 'live':
            query = """
                SELECT * FROM (
                    SELECT DISTINCT ON (e.event_id) e.event_id, 
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts :: TIMESTAMP AS starts,
                        l.created_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                    JOIN api_request_logs l ON l.event_id = e.event_id 
                    WHERE
                        e.sport_uname = %s 
                        AND e.league_uname = %s 
                        AND e.event_type = 'prematch'
                        AND l.created_at AT TIME ZONE 'UTC' <= e.starts
                    ORDER BY
                        e.event_id,
                        l.created_at DESC 
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC;
            """
        else:
            query = """
                SELECT * FROM (
                    SELECT DISTINCT ON (e.event_id) e.event_id, 
                        home_team,
                        away_team,
                        league_name,
                        starts :: TIMESTAMP AS starts,
                        archived_at AT TIME ZONE 'UTC'
                    FROM
                        events
                    WHERE
                        sport_uname = %s 
                        AND league_uname = %s 
                        AND event_type = 'prematch'
                    ORDER BY
                        event_id,
                        archived_at DESC 
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC;
            """

        cursor.execute(query, (sport_name, league_name))
        events = cursor.fetchall()
        
        result = [
            {
                'event_id': event[0],
                'home_team': event[1],
                'away_team': event[2],
                'league_name': event[3],
                'starts': event[4],
                'updated_at': event[5]
            } for event in events
        ]
        
        return result
    elif sport_name != '' and league_name == '' and team_name != '':
        if type == 'live':
            query = """
                SELECT * FROM (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts::TIMESTAMP AS starts,
                        l.created_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                    JOIN api_request_logs l ON l.event_id = e.event_id
                    WHERE
                        e.sport_uname = %s
                        AND (e.home_team_uname = %s OR e.away_team_uname = %s)
                        AND e.event_type = 'prematch'
                        AND l.created_at AT TIME ZONE 'UTC' <= e.starts
                    ORDER BY
                        event_id,
                        archived_at DESC
                ) AS tmp
                ORDER BY 
                    tmp.starts DESC;
            """
        else:
            query = """
                SELECT * FROM (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts::TIMESTAMP AS starts,
                        e.archived_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                    WHERE
                        e.sport_uname = %s
                        AND (e.home_team_uname = %s OR e.away_team_uname = %s)
                        AND e.event_type = 'prematch'
                    ORDER BY
                        e.event_id,
                        e.archived_at DESC
                ) AS tmp
                ORDER BY 
                    tmp.starts DESC;
            """

        cursor.execute(query, (sport_name, team_name, team_name))

        events = cursor.fetchall()
        result = [
            {
                'event_id': event[0],
                'home_team': event[1],
                'away_team': event[2],
                'league_name': event[3],
                'starts': event[4],
                'updated_at': event[5]
            } for event in events
        ]
        
        return result  
    elif league_name != '' and team_name != '':
        if type == 'live':
            query = """
                SELECT
                * 
                FROM
                (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts :: TIMESTAMP AS starts,
                        l.created_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                        JOIN api_request_logs l ON l.event_id = e.event_id 
                    WHERE
                        e.sport_uname = %s 
                        AND e.league_uname = %s 
                        AND ( e.home_team_uname = %s OR e.away_team_uname = %s ) 
                        AND e.event_type = 'prematch'
                        AND l.created_at AT TIME ZONE 'UTC' <= e.starts
                    ORDER BY
                        e.event_id,
                        l.created_at DESC
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC;
            """
        else:
            query = """
                SELECT
                * 
                FROM
                (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts :: TIMESTAMP AS starts,
                        e.archived_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                    WHERE
                        e.sport_uname = %s 
                        AND e.league_uname = %s 
                        AND ( e.home_team_uname = %s OR e.away_team_uname = %s ) 
                        AND e.event_type = 'prematch'
                    ORDER BY
                        e.event_id,
                        e.archived_at DESC
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC;
            """

        cursor.execute(query, (sport_name, league_name, team_name, team_name))
        events = cursor.fetchall()
        
        result = [
            {
                'event_id': event[0],
                'home_team': event[1],
                'away_team': event[2],
                'league_name': event[3],
                'starts': event[4],
                'updated_at': event[5],
            } for event in events
        ]
        
        return result
    elif sport_name == '' and league_name == '' and team_name != '':
        if type == 'live':
            query = """
                SELECT
                * 
                FROM
                (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts :: TIMESTAMP AS starts,
                        l.created_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                        JOIN api_request_logs l ON l.event_id = e.event_id 
                    WHERE
                        e.home_team_uname = %s OR e.away_team_uname = %s 
                        AND e.event_type = 'prematch'
                        AND l.created_at AT TIME ZONE 'UTC' <= e.starts
                    ORDER BY
                        e.event_id,
                        l.created_at DESC
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC; 
            """
        else:
            query = """
                SELECT
                    * 
                FROM
                (
                    SELECT DISTINCT ON (e.event_id) e.event_id,
                        e.home_team,
                        e.away_team,
                        e.league_name,
                        e.starts :: TIMESTAMP AS starts,
                        e.archived_at AT TIME ZONE 'UTC'
                    FROM
                        events e
                    WHERE
                        e.home_team_uname = %s OR e.away_team_uname = %s 
                        AND e.event_type = 'prematch'
                    ORDER BY
                        e.event_id,
                        e.archived_at DESC
                ) AS tmp 
                ORDER BY
                    tmp.starts DESC; 
            """

        cursor.execute(query, (team_name, team_name))

        events = cursor.fetchall()
        
        result = [
            {
                'event_id': event[0],
                'home_team': event[1],
                'away_team': event[2],
                'league_name': event[3],
                'starts': event[4],
                'updated_at': event[5],
            } for event in events
        ]
        
        return result


# @app.get("/archive/{sport_name}/{league_name}/{team_name}/{event_id}")
# async def archive_data(sport_name: str, league_name: str = 'l', team_name: str = 't', event_id: str = 'e'):
#     if sport_name and event_id != 'e':
#         return await receive_event(event_id)
#     else:
#         return await receive_event_info(sport_name, league_name, team_name)
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info('starting the websocket backend...')
    await manager.connect(websocket)
    
    while True:
        try: 
            # await websocket.receive_text()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("LISTEN odds_update;")

            while True:
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop()
                    data = json.loads(notify.payload)
                    await websocket.send_json(data)
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(e)
            await websocket.close()
            break
        finally:
            manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)