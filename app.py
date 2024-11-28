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
                WITH MaxTime AS (
                    SELECT period_id, MAX(time) AS max_time
                    FROM money_lines
                    WHERE period_id = %s
                    GROUP BY period_id
                )
                SELECT ml.home_odds, ml.draw_odds, ml.away_odds, ml.max_bet
                FROM money_lines ml
                JOIN MaxTime mt
                ON ml.period_id = mt.period_id AND ml.time = mt.max_time
                WHERE ml.period_id = %s
                ORDER BY ml.period_id;
            """, (period, period))
            money_line = cursor.fetchall()

            # Query to get the spread data for a specific period_id
            cursor.execute("""
                WITH MaxTime AS (
                    SELECT MAX(time) AS max_time
                    FROM spreads
                    WHERE period_id = %s
                )
                SELECT handicap, home_odds, away_odds, max_bet
                FROM spreads
                JOIN MaxTime
                ON spreads.time = MaxTime.max_time
                WHERE spreads.period_id = %s
                ORDER BY handicap ASC;
            """, (period, period))
            spread = cursor.fetchall()

            # Query to get the total data for a specific period_id
            cursor.execute("""
                WITH MaxTime AS (
                    SELECT MAX(time) AS max_time
                    FROM totals
                    WHERE period_id = %s
                )
                SELECT points, over_odds, under_odds, max_bet
                FROM totals t
                JOIN MaxTime mt
                ON t.time = mt.max_time
                WHERE t.period_id = %s
                ORDER BY t.points ASC;
            """, (period,period))
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
async def receive_chart_event(period_id: str, hdp: float):
    try: 
        # Add the received event_id to the storage
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get period_ids by event_id
        cursor.execute("""
            SELECT home_odds, away_odds, time FROM spreads WHERE period_id = %s and handicap = %s ORDER BY time ASC LIMIT 20
        """, (period_id, hdp))

        spreads = cursor.fetchall()
        result = [{
            'time': spread[2].strftime('%m-%d %H:%M'),
            'home': spread[0], 
            'away': spread[1]
        } for spread in spreads]
        
        return {"message": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in /receive-chart-event: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while fetching chart data")

@app.get("/receive-options-event")
async def receive_options_event(sport_id: int = None):
    logger.info('starting receive-options...')
    if sport_id is None:
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
    else:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT league_id, league_name
            FROM events
            WHERE sport_id = %s ORDER BY league_name ASC;
        """, (sport_id,))

        leagues = cursor.fetchall()
        result = [{
            'value': league[0],
            'label': league[1], 
        } for league in leagues]
        
        return result

@app.get("/receive-event-info")
async def receive_event_info(sport_id: int, league_id: int):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT event_id, home_team, away_team, last_updated
        FROM events
        WHERE sport_id = %s AND league_id = %s
        ORDER BY last_updated DESC
        LIMIT 20;
    """, (sport_id, league_id))

    events = cursor.fetchall()
    
    result = [
        {
            'event_id': event[0],
            'home_team': event[1],
            'away_team': event[2],
            'updated_at': event[3]
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