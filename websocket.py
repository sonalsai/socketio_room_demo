import os
import base64
import json
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration constants
CONFIG = {
    "PORT": 8080,
    "SAMPLE_RATE": 8000,
    "ENCODING": "mulaw",  # Twilio's PCMU format
    "CHANNELS": 1
}

# Deepgram WebSocket URL with parameters for PCMU
DEEPGRAM_SOCKET_URL = (
    f"wss://api.deepgram.com/v1/listen"
    f"?encoding={CONFIG['ENCODING']}"
    f"&sample_rate={CONFIG['SAMPLE_RATE']}"
    f"&channels={CONFIG['CHANNELS']}"
)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Initialize FastAPI
app = FastAPI()

# WebSocket endpoint for Twilio to connect to FastAPI
@app.websocket("/twilio")
async def twilio_ws(websocket: WebSocket):
    await websocket.accept()
    print("Received connection from Twilio")

    try:
        # Set up a WebSocket connection to Deepgram's streaming API
        async with websockets.connect(
            DEEPGRAM_SOCKET_URL,
            extra_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        ) as deepgram_ws:
            print("Connected to Deepgram WebSocket for transcription")

            async def receive_from_twilio():
                while True:
                    try:
                        # Receive message from Twilio
                        message = await websocket.receive_text()
                        data = json.loads(message)

                        # Only process media events with payload
                        if data["event"] == "media" and data["media"].get("payload"):
                            # Decode base64-encoded PCMU payload
                            pcmu_buffer = base64.b64decode(data["media"]["payload"])
                            # Send to Deepgram
                            await deepgram_ws.send(pcmu_buffer)
                    except WebSocketDisconnect:
                        print("Twilio WebSocket disconnected")
                        break
                    except Exception as error:
                        print(f"Error processing Twilio message: {error}")

            async def receive_from_deepgram():
                while True:
                    try:
                        # Receive message from Deepgram
                        deepgram_message = await deepgram_ws.recv()

                        # Parse and process transcription data
                        transcription_data = json.loads(deepgram_message)
                        if transcription_data and transcription_data.get("channel") and transcription_data["channel"]["alternatives"]:
                            transcription = transcription_data["channel"]["alternatives"][0].get("transcript")
                            if transcription:
                                print("Transcription text:", transcription)
                    except websockets.exceptions.ConnectionClosed:
                        print("Deepgram WebSocket closed")
                        break
                    except Exception as error:
                        print(f"Error processing Deepgram response: {error}")

            # Run both Twilio and Deepgram receivers concurrently
            await asyncio.gather(receive_from_twilio(), receive_from_deepgram())

    except Exception as error:
        print("Error connecting to Deepgram WebSocket:", error)
        if "401" in str(error):
            print("""
Authentication Error: Please check your Deepgram API key:
1. Verify the key in your .env file
2. Ensure the key hasn't expired
3. Check if the key has the necessary permissions
            """)

    finally:
        await websocket.close()
        print("Connection closed")


# Run the server using Hypercorn or Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=CONFIG["PORT"])
