import uvicorn
import socketio
from fastapi import FastAPI

# FastAPI application
app = FastAPI()

# SocketIO server with CORS allowed
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

# Wrap Socket.IO in an ASGI app
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)


@app.get("/")
async def index():
    return {"Hello": "World"}


# Event: New client connects
@sio.on("connect")
async def connect(sid, environ):
    print(f"Client connected with session id: {sid}")


# Event: Client disconnects
@sio.on("disconnect")
async def disconnect(sid):
    print(f"Client disconnected with session id: {sid}")


# Event: Receiving audio data
@sio.on("audioChunk")
async def handle_audio(sid, data):
    # Save or process the received audio chunk
    print(f"Received audio chunk from {sid}: {len(data)} bytes")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7777, lifespan="on", reload=True)
