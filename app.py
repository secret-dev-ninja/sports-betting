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

def get_uname(text: str) -> str:
    return text.lower().replace('(', '').replace(')', '').replace(' ', '-').replace('---', '-')

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
            WHERE event_id = %s ORDER BY period_number ASC;
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
                    ml.time AT TIME ZONE 'UTC' AS time
                FROM
                    money_lines ml
                JOIN periods p ON ml.period_id = p.period_id
                WHERE
                    p.period_id = %s
                    AND ml.time AT TIME ZONE 'UTC' <= p.cutoff
                ORDER BY
                    ml.time DESC
                LIMIT 1
            """, (period))
            money_line = cursor.fetchall()

            # Query to get the spread data for a specific period_id
            cursor.execute("""
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
                    AND P.cutoff >= s.time AT TIME ZONE 'UTC'
                ORDER BY
                    s.handicap,
                    s.time DESC;
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
                    t.time AT TIME ZONE 'UTC' AS time
                FROM 
                    totals t
                JOIN periods p ON t.period_id = p.period_id
                WHERE 
                    t.period_id = %s
                    AND p.cutoff >= t.time AT TIME ZONE 'UTC'
                ORDER BY 
                    t.points, t.time DESC;
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
                    ( SELECT s.home_odds, s.away_odds, s.time AT TIME ZONE 'UTC' AS time, s.max_bet
                    FROM spreads s
                    JOIN periods p ON s.period_id = p.period_id
                    WHERE s.period_id = %s AND s.handicap = %s AND p.cutoff >= s.time AT TIME ZONE 'UTC'
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
                    ( SELECT ml.home_odds, ml.away_odds, ml.time AT TIME ZONE 'UTC' AS time, ml.max_bet
                    FROM money_lines ml
                    JOIN periods p ON ml.period_id = p.period_id
                    WHERE ml.period_id = %s AND p.cutoff >= ml.time AT TIME ZONE 'UTC'
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
                    ( SELECT t.over_odds, t.under_odds, t.time AT TIME ZONE 'UTC' AS time, t.max_bet
                    FROM totals t
                    JOIN periods p ON t.period_id = p.period_id
                    WHERE t.period_id = %s and t.points = %s AND p.cutoff >= t.time AT TIME ZONE 'UTC'
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
async def receive_options_event(sport_name: str = None, league_name: str = 'l'):
    if sport_name is None and league_name == 'l':
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
    elif sport_name is not None and league_name == 'l':
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
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
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
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
async def receive_event_info(sport_name: str, league_name: str = 'l', team_name: str = 't'):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    if league_name != 'l' and team_name == 't':
        cursor.execute("""
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
        """, (sport_name, league_name))

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
    elif league_name == 'l' and team_name != 't':
        cursor.execute("""
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
                    e.event_id,
                    l.created_at DESC
            ) AS tmp
            ORDER BY 
                tmp.starts DESC;
        """, (sport_name, team_name, team_name))

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
    elif league_name != 'l' and team_name != 't':
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
        """, (sport_name, league_name, team_name, team_name))

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

@app.get("/archive/{sport_name}/{league_name}/{team_name}/{event_id}")
async def archive_data(sport_name: str, league_name: str = 'l', team_name: str = 't', event_id: str = 'e'):
    if sport_name and event_id != 'e':
        return await receive_event(event_id)
    else:
        return await receive_event_info(sport_name, league_name, team_name)
    
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