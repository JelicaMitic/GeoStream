from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.routers import drivers, rides
from app.database import engine
from app import models
from app.logger import logger
from typing import List

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeoStream API")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Novi WebSocket klijent, ukupno: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Klijent se diskonektovao, ukupno: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
app.state.manager = manager

app.include_router(drivers.router)
app.include_router(rides.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def root():
    return {"message": "GeoStream API radi!"}