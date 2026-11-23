import os
import re
import asyncio
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient, functions, errors
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
SERVICE_KEY = os.environ["SERVICE_KEY"]
print("SESSION LENGTH:", len(SESSION_STRING))
print("SESSION EMPTY:", not bool(SESSION_STRING.strip()))
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
check_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError("Telegram session is not authorized. Create a new session string.")
    yield
    await client.disconnect()

app = FastAPI(title="Username Forge Checker", lifespan=lifespan)

class CheckRequest(BaseModel):
    key: str
    username: str

@app.get("/")
async def home():
    return {"service": "Username Forge Checker", "status": "online"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/check")
async def check_username(data: CheckRequest):
    if not secrets.compare_digest(data.key, SERVICE_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")

    username = data.username.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", username):
        raise HTTPException(status_code=400, detail="Invalid Telegram username format")

    # Check sequentially to reduce the risk of Telegram flood limits.
    async with check_lock:
        try:
            available = await client(functions.account.CheckUsernameRequest(username=username))
            await asyncio.sleep(0.7)
            return {"username": username, "available": bool(available), "verified": True}
        except errors.UsernameOccupiedError:
            return {"username": username, "available": False, "verified": True}
        except errors.UsernameInvalidError:
            return {"username": username, "available": False, "verified": True}
        except errors.FloodWaitError as exc:
            raise HTTPException(status_code=429, detail=f"Telegram rate limit. Retry after {exc.seconds} seconds.")
        except errors.RPCError:
            raise HTTPException(status_code=503, detail="Telegram could not verify this username. Try again later.")
