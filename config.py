import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

CONFIG = {
    "SAMPLE_RATE": 48000,
    "ENCODING": "opus",
    "CHANNELS": 1,
    "DEEPGRAM_SOCKET_URL": (
        f"wss://api.deepgram.com/v1/listen"
        f"?encoding=opus&sample_rate=48000&channels=1"
    )
}
