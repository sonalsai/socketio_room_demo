import json
import websockets
import asyncio
from config import CONFIG, DEEPGRAM_API_KEY
import socketio

# Function to connect to Deepgram WebSocket
async def connect_to_deepgram():
    try:
        return await websockets.connect(
            CONFIG["DEEPGRAM_SOCKET_URL"],
            extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        )
    except Exception as e:
        print(f"Error connecting to Deepgram: {e}")
        return None

# Process transcriptions from Deepgram and emit them to the client
async def process_transcriptions(deepgram_ws, sid, sio: socketio.AsyncServer):
    try:
        async for message in deepgram_ws:
            data = json.loads(message)
            transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript")
            if transcript:
                await sio.emit("transcription", {"text": transcript}, to=sid)
                print(f"Transcription for {sid}: {transcript}")
    except websockets.exceptions.ConnectionClosed:
        print("Deepgram WebSocket closed")
    except Exception as e:
        print(f"Error processing transcription for {sid}: {e}")
