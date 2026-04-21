import os
import time
import json
import logging
from typing import Optional

import requests
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

EMBY_URL = os.getenv("EMBY_URL", "http://emby:8096")
EMBY_API_KEY = os.getenv("EMBY_API_KEY", "")
EMBY_USER_ID = os.getenv("EMBY_USER_ID", "")
EMBY_DEVICE_NAME = os.getenv("EMBY_DEVICE_NAME", "")  # optional filter
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_KEY = os.getenv("REDIS_KEY", "emby:last_session")

session = requests.Session()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def emby_get(path: str, params: Optional[dict] = None):
    if params is None:
        params = {}
    params["api_key"] = EMBY_API_KEY
    url = EMBY_URL.rstrip("/") + path
    resp = session.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


def emby_post(path: str, data: Optional[dict] = None, params: Optional[dict] = None):
    if params is None:
        params = {}
    params["api_key"] = EMBY_API_KEY
    url = EMBY_URL.rstrip("/") + path
    resp = session.post(url, params=params, json=data or {}, timeout=5)
    resp.raise_for_status()
    return resp.json() if resp.content else None


def get_active_session():
    sessions = emby_get("/Sessions")
    for s in sessions:
        if EMBY_USER_ID and s.get("UserId") != EMBY_USER_ID:
            continue
        if EMBY_DEVICE_NAME and s.get("DeviceName") != EMBY_DEVICE_NAME:
            continue
        if s.get("NowPlayingItem"):
            return s
    return None


def get_play_queue(session_id: str):
    # Not all Emby versions expose this; fallback is just current item
    try:
        return emby_get(f"/Sessions/{session_id}/PlayQueue")
    except Exception as e:
        logging.warning("Failed to get play queue: %s", e)
        return None


def save_session_state():
    try:
        s = get_active_session()
        if not s:
            logging.debug("No active session found")
            return

        session_id = s["Id"]
        now_playing = s.get("NowPlayingItem")
        if not now_playing:
            return

        position_ticks = s.get("PlayState", {}).get("PositionTicks", 0)
        queue = get_play_queue(session_id)

        state = {
            "session_id": session_id,
            "user_id": s.get("UserId"),
            "device_name": s.get("DeviceName"),
            "now_playing_id": now_playing.get("Id"),
            "position_ticks": position_ticks,
            "queue": queue,
        }

        r.set(REDIS_KEY, json.dumps(state))
        logging.info(
            "Saved session: item=%s position=%s",
            now_playing.get("Name"),
            position_ticks,
        )
    except Exception as e:
        logging.error("Error saving session state: %s", e)


def restore_session_state():
    try:
        raw = r.get(REDIS_KEY)
        if not raw:
            logging.info("No saved session state in Redis")
            return

        state = json.loads(raw)
        item_id = state.get("now_playing_id")
        position_ticks = state.get("position_ticks", 0)

        if not item_id:
            logging.info("Saved state has no item_id")
            return

        logging.info(
            "Restoring session: item_id=%s position_ticks=%s",
            item_id,
            position_ticks,
        )

        # Find a current session for this user/device
        s = get_active_session()
        if not s:
            logging.info("No active session to restore into")
            return

        session_id = s["Id"]

        # Start playback of the item at the saved position
        # This uses the "Playing" API to set the current item and position
        emby_post(
            f"/Sessions/{session_id}/Playing",
            data={
                "ItemId": item_id,
                "CanSeek": True,
                "PositionTicks": position_ticks,
                "PlayCommand": "PlayNow",
            },
        )

        logging.info("Restore request sent to Emby")
    except Exception as e:
        logging.error("Error restoring session state: %s", e)


def main():
    logging.info("Starting Emby session service")
    if not EMBY_API_KEY:
        logging.error("EMBY_API_KEY is required")
        return

    # Try to restore on startup
    restore_session_state()

    # Poll loop
    while True:
        save_session_state()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
