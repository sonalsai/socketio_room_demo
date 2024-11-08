import base64
import asyncio
from deepgram_ws import connect_to_deepgram, process_transcriptions

async def handle_connect(sid, environ, sio):
    print(f"Client connected: {sid}")
    deepgram_ws = await connect_to_deepgram()
    environ["deepgram_ws"] = deepgram_ws

    # Start transcription processing if the connection to Deepgram is established
    if deepgram_ws:
        asyncio.create_task(process_transcriptions(deepgram_ws, sid, sio))

async def handle_disconnect(sid, environ):
    print(f"Client disconnected: {sid}")
    deepgram_ws = environ.pop("deepgram_ws", None)
    if deepgram_ws and deepgram_ws.open:
        await deepgram_ws.close()

async def handle_audio_chunk(sid, data, environ):
    deepgram_ws = environ.get("deepgram_ws")
    if deepgram_ws and deepgram_ws.open:
        audio_chunk = base64.b64decode(data)
        await deepgram_ws.send(audio_chunk)
