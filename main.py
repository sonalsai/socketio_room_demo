import os
import json
import asyncio
import base64
import uvicorn
import socketio
import websockets
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration constants
CONFIG = {
    "SAMPLE_RATE": 48000,  # Opus standard sample rate for webm audio
    "ENCODING": "opus",  # Specify opus encoding for webm audio
    "CHANNELS": 1,  # Set number of audio channels
}

# Deepgram WebSocket URL configured for webm with opus encoding
DEEPGRAM_SOCKET_URL = (
    f"wss://api.deepgram.com/v1/listen"
    f"?encoding={CONFIG['ENCODING']}"
    f"&sample_rate={CONFIG['SAMPLE_RATE']}"
    f"&channels={CONFIG['CHANNELS']}"
)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# FastAPI application
app = FastAPI()

# Socket.IO server with CORS allowed
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")

# Wrap Socket.IO in an ASGI app
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)


# Event: New client connects
@sio.on("connect")
async def connect(sid, environ):
    print(f"Client connected with session id: {sid}")
    # Open connection to Deepgram for each client
    environ["deepgram_ws"] = await connect_to_deepgram()


# Event: Client disconnects
@sio.on("disconnect")
async def disconnect(sid, environ):
    print(f"Client disconnected with session id: {sid}")
    # Close Deepgram WebSocket if open
    deepgram_ws = environ.get("deepgram_ws")
    if deepgram_ws and deepgram_ws.open:
        await deepgram_ws.close()


# Connect to Deepgram WebSocket
async def connect_to_deepgram():
    try:
        deepgram_ws = await websockets.connect(
            DEEPGRAM_SOCKET_URL,
            extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        )
        print("Connected to Deepgram WebSocket for transcription")
        return deepgram_ws
    except Exception as e:
        print("Error connecting to Deepgram WebSocket:", e)
        return None


# Event: Receiving webm audio data from client
@sio.on("audioChunk")
async def handle_audio(sid, data, environ):
    # Decode base64 webm audio data and send to Deepgram
    webm_chunk = base64.b64decode(data)
    deepgram_ws = environ.get("deepgram_ws")

    # Send to Deepgram if connection is open
    if deepgram_ws and deepgram_ws.open:
        await deepgram_ws.send(webm_chunk)

    # Process Deepgram transcription response
    asyncio.create_task(process_transcription(deepgram_ws, sid))


# Process transcription data from Deepgram and emit to client
async def process_transcription(deepgram_ws, sid):
    try:
        async for message in deepgram_ws:
            # Parse transcription data
            transcription_data = json.loads(message)
            if (
                transcription_data
                and transcription_data.get("channel")
                and transcription_data["channel"]["alternatives"]
            ):
                transcription = transcription_data["channel"]["alternatives"][0].get(
                    "transcript"
                )
                if transcription:
                    # Send transcription back to client
                    await sio.emit("transcription", {"text": transcription}, to=sid)
                    print(f"Transcription sent to {sid}: {transcription}")
    except websockets.exceptions.ConnectionClosed:
        print("Deepgram WebSocket closed")
    except Exception as e:
        print("Error processing Deepgram response:", e)


# FastAPI route for basic check
@app.get("/")
async def index():
    return {"Hello": "World"}


# Run the server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7777, lifespan="on", reload=True)
