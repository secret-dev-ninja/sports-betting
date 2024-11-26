from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import asyncio
import logging
from typing import List
from dotenv import load_dotenv
from config import DB_CONFIG
from datetime import datetime

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
        self.active_connections.remove(websocket)
        logger.info("WebSocket connection closed.")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info('starting the websocket backend...')    
    await manager.connect(websocket)
    
    while True:
        try: 
            # await websocket.receive_text()
            conn = psycopg2.connect(**DB_CONFIG)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN odds_update;")

            while True:
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop()
                    await websocket.send_json(json.loads(notify.payload))

                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(e)
            break

@app.get("/receive-event")
async def receive_event(event_id: str):
    try:
        # Add the received event_id to the storage
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
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
                "money_line": money_line if money_line else [],
                "spread": spread if spread else [],
                "total": total if total else []
            })

        return {"message": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/receive-chart-event")
async def receive_chart_event(period_id: str, hdp: float):
    # Add the received event_id to the storage
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Query to get period_ids by event_id
    cursor.execute("""
        SELECT home_odds, away_odds, time FROM spreads WHERE period_id = %s and handicap = %s ORDER BY time ASC LIMIT 100
    """, (period_id, hdp))

    spreads = cursor.fetchall()
    result = [{
        'time': spread[2].strftime('%m-%d %H:%M'),
        'home': spread[0], 
        'away': spread[1]
    } for spread in spreads]
    
    return {"message": "success", "data": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)