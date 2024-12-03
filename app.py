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

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/receive-event")
async def receive_event(event_id: str):
    try:
        # Add the received event_id to the storage
        conn = get_db_connection()
        cursor = conn.cursor()

         # Query to get period_ids by event_id
        cursor.execute("""
            SELECT period_id
            FROM periods
            WHERE event_id = %s;
        """, (event_id,))



        periods = cursor.fetchall()

        # If no periods are found for the given event_id
        if not periods:
            raise HTTPException(status_code=404, detail="No periods found for the provided event_id")
        
        result = []
        for period in periods:
            # Query to get the money_line data for a specific period_id
            cursor.execute("""
                SELECT 
                    ml.home_odds,
                    ml.draw_odds,
                    ml.away_odds,
                    ml.max_bet,
                    ml.time::timestamp as time
                FROM
                    money_lines ml
                JOIN periods p ON ml.period_id = p.period_id 
                WHERE
                    p.period_id = %s
                ORDER BY
                    time DESC 
                LIMIT 1
            """, (period))
            money_line = cursor.fetchall()

            # Query to get the spread data for a specific period_id
            cursor.execute("""
               SELECT 
                    DISTINCT ON (handicap)
                    s.handicap,
                    s.home_odds, 
                    s.away_odds, 
                    s.max_bet,
                    s.time::timestamp as time
                FROM spreads s
                JOIN periods p ON s.period_id = p.period_id
                WHERE s.period_id = %s
                ORDER BY s.handicap, s.time DESC;
            """, (period,))
            spread = cursor.fetchall()

            # Query to get the total data for a specific period_id
            cursor.execute("""
                SELECT 
                    DISTINCT ON (points)
                    t.points, 
                    t.over_odds, 
                    t.under_odds, 
                    t.max_bet,
                    t.time::timestamp as time
                FROM totals t
                JOIN periods p ON t.period_id = p.period_id
                WHERE t.period_id = %s
                ORDER BY t.points, t.time DESC;
            """, (period,))
            total = cursor.fetchall()

            # Append the result as a dictionary
            result.append({
                "period_id": period,
                "money_line": money_line or [],
                "spread": spread or [],
                "total": total or []
            })

        return {"message": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in /receive-event: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/receive-chart-event")
async def receive_chart_event(period_id: str, hdp: float = None, points: float = None, type: str = None):
    if type == 'spread':
        try: 
            # Add the received event_id to the storage
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to get period_ids by event_id
            cursor.execute("""
                SELECT
                    * 
                FROM
                    ( SELECT s.home_odds, s.away_odds, s.time::timestamp as time, s.max_bet
                    FROM spreads s
                    JOIN periods p ON s.period_id = p.period_id
                    WHERE s.period_id = %s AND s.handicap = %s 
                    ORDER BY s.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """, (period_id, hdp))

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
    elif type == 'money_line':
        try: 
            # Add the received event_id to the storage
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to get period_ids by event_id
            cursor.execute("""
                SELECT
                    * 
                FROM
                    ( SELECT ml.home_odds, ml.away_odds, ml.time::timestamp as time, ml.max_bet
                    FROM money_lines ml
                    JOIN periods p ON ml.period_id = p.period_id
                    WHERE ml.period_id = %s 
                    ORDER BY ml.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """, (period_id,))

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
    elif type == 'total':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    * 
                FROM
                    ( SELECT t.over_odds, t.under_odds, t.time::timestamp as time, t.max_bet
                    FROM totals t
                    JOIN periods p ON t.period_id = p.period_id
                    WHERE t.period_id = %s and t.points = %s
                    ORDER BY t.time DESC LIMIT 30 ) tmp 
                ORDER BY
                    tmp.time ASC
            """, (period_id, points))

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
async def receive_options_event(sport_id: int = None, league_id: int = None):
    if sport_id is None and league_id is None:
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
            
            sports =  [{"value": sport['id'], "label": sport['name']} for sport in data]
            return sports
            
        except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                return None
    elif sport_id is not None and league_id is None:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT league_id, league_name
            FROM events
            WHERE sport_id = %s ORDER BY league_name ASC;
        """, (sport_id,))

        leagues = cursor.fetchall()
        leaguesOpts = [{
            'value': league[0],
            'label': league[1], 
        } for league in leagues]

        cursor.execute("""
        SELECT DISTINCT team
        FROM (
            SELECT home_team AS team
            FROM events
            WHERE sport_id = %s
            UNION ALL
            SELECT away_team AS team
            FROM events
            WHERE sport_id = %s
        ) AS combined_teams ORDER BY team ASC;
        """, (sport_id, sport_id))
    
        teams = cursor.fetchall()
        teamsOpts = [{
            'value': team[0],
            'label': team[0],
        } for team in teams]

        return {
            'leagues': leaguesOpts,
            'teams': teamsOpts
        }
    elif sport_id is not None and league_id is not None:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        logger.info('starting receive-options...%s, %s', sport_id, league_id)

        cursor.execute("""
        SELECT DISTINCT team
        FROM (
            SELECT home_team AS team
            FROM events
            WHERE sport_id = %s
            AND league_id = %s
            UNION ALL
            SELECT away_team AS team
            FROM events
            WHERE sport_id = %s
            AND league_id = %s
        ) AS combined_teams ORDER BY team ASC;
        """, (sport_id, league_id, sport_id, league_id))

        teams = cursor.fetchall()
        result = [{
            'value': team[0],
            'label': team[0],
        } for team in teams]

        return result

@app.get("/receive-event-info")
async def receive_event_info(sport_id: int, league_id: int = None, team_name: str = None):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    if team_name is None:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM (
                SELECT DISTINCT ON (e.event_id) e.event_id, 
                    e.home_team,
                    e.away_team,
                    e.league_name,
                    e.starts :: TIMESTAMP AS starts,
                    l.created_at 
                FROM
                    events e
                JOIN api_request_logs l ON l.event_id = e.event_id 
                WHERE
                    e.sport_id = %s 
                    AND e.league_id = %s 
                    AND e.event_type = 'prematch' 
                    AND l.created_at <= e.starts 
                ORDER BY
                    e.event_id,
                    l.created_at DESC 
            ) AS tmp 
            ORDER BY
                tmp.starts DESC;
        """, (sport_id, league_id))

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
    elif league_id is None and team_name is not None:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM (
                SELECT DISTINCT ON (e.event_id) e.event_id,
                    e.home_team,
                    e.away_team,
                    e.league_name,
                    e.starts::TIMESTAMP AS starts,
                    l.created_at
                FROM
                    events e
                JOIN api_request_logs l ON l.event_id = e.event_id
                WHERE
                    e.sport_id = %s
                    AND (e.home_team = %s OR e.away_team = %s)
                    AND e.event_type = 'prematch'
                    AND l.created_at <= e.starts 
                ORDER BY
                    e.event_id,
                    l.created_at DESC
            ) AS tmp
            ORDER BY 
                tmp.starts DESC;
        """, (sport_id, team_name, team_name))

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
    else:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
            * 
            FROM
            (
                SELECT DISTINCT ON (e.event_id) e.event_id,
                    e.home_team,
                    e.away_team,
                    e.league_name,
                    e.starts :: TIMESTAMP AS starts,
                    l.created_at 
                FROM
                    events e
                    JOIN api_request_logs l ON l.event_id = e.event_id 
                WHERE
                    e.sport_id = %s 
                    AND e.league_id = %s 
                    AND ( e.home_team = %s OR e.away_team = %s ) 
                    AND e.event_type = 'prematch' 
                    AND l.created_at <= e.starts 
                ORDER BY
                    e.event_id,
                    l.created_at DESC
            ) AS tmp 
            ORDER BY
                tmp.starts DESC;
        """, (sport_id, league_id, team_name, team_name))

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