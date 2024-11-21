from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import json
import asyncio
import logging
from typing import List, Dict
from dotenv import load_dotenv
from config import DB_CONFIG

# Load environment variables
load_dotenv()

# Set up logging for debugging
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

# WebSocket Connection Manager
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

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# Database Listener for PostgreSQL Notifications
class DBListener:
    def __init__(self):
        logger.info("Setting up database listener.")
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor()

    def setup_triggers(self):
        logger.info("Setting up triggers in the database.")
        # Create notification function
        self.cur.execute("""
        CREATE OR REPLACE FUNCTION notify_odds_update() RETURNS TRIGGER AS $$
        DECLARE
            event_data json;
        BEGIN
            SELECT json_build_object(
                'event_id', e.event_id,
                'home_team', e.home_team,
                'away_team', e.away_team,
                'table_updated', TG_TABLE_NAME,
                'update_time', CURRENT_TIMESTAMP
            ) INTO event_data
            FROM events e
            WHERE e.event_id = NEW.event_id;

            PERFORM pg_notify('odds_update', event_data::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)

        # Create triggers for relevant tables
        triggers = ["money_lines", "spreads", "totals", "team_totals"]
        for table in triggers:
            self.cur.execute(f"""
            DROP TRIGGER IF EXISTS {table}_notify_trigger ON {table};
            CREATE TRIGGER {table}_notify_trigger
                AFTER INSERT ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION notify_odds_update();
            """)

    async def listen(self):
        logger.info("Listening for notifications.")
        self.cur.execute("LISTEN odds_update;")
        while True:
            self.conn.poll()
            while self.conn.notifies:
                notify = self.conn.notifies.pop()
                await manager.broadcast(json.loads(notify.payload))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application.")
    
    # Initialize the database listener
    db_listener = DBListener()
    logger.info("Database listener created.")
    
    try:
        db_listener.setup_triggers()
        logger.info("Database triggers set up.")
    except Exception as e:
        logger.error(f"Error setting up triggers: {e}")
        raise

    try:
        asyncio.create_task(db_listener.listen())
        logger.info("Started database listener task.")
    except Exception as e:
        logger.error(f"Error starting database listener: {e}")
        raise
    
    logger.info("WebSocket backend has started.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
