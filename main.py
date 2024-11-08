import uvicorn
import socketio
from fastapi import FastAPI
from socket_events import handle_connect, handle_disconnect, handle_audio_chunk

# Initialize FastAPI app and Socket.IO server
app = FastAPI()
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)

# Socket.IO event registrations
@sio.on("connect")
async def on_connect(sid, environ):
    await handle_connect(sid, environ, sio)

@sio.on("disconnect")
async def on_disconnect(sid, environ):
    await handle_disconnect(sid, environ)

@sio.on("audioChunk")
async def on_audio_chunk(sid, data, environ):
    await handle_audio_chunk(sid, data, environ)

# FastAPI route for basic check
@app.get("/")
async def index():
    return {"message": "Hello, World"}

# Run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7777, lifespan="on", reload=True)
