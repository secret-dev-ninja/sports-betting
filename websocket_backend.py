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
import random

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_backend")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost:3000"],  # In production, replace with your frontend URL
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
            await websocket.receive_text()
            
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)