from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os
import sys
import requests
from typing import List, Dict

app = FastAPI()

LLAMA_URL = os.getenv(
    "LLAMA_URL",
    "http://llama-cpp.llama-cpp.svc.cluster.local:8080/v1/chat/completions"
)

# In-memory conversation store
conversations: Dict[str, List[tuple]] = {}

# -----------------------------
# Tavily web search (sync OK)
# -----------------------------
def search_web(query: str):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return ["No TAVILY_API_KEY - using mock context"]

    r = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "query": query,
            "search_depth": "basic",
            "max_results": 3,
        },
        timeout=15,
    )

    if r.status_code != 200:
        return [f"Search API error: {r.status_code}"]

    data = r.json()
    return [item.get("content", "") for item in data.get("results", [])]


# -------------------------------------------------
# llama.cpp streaming generator (ONLY yields)
# -------------------------------------------------
async def ask_llama_stream(messages: list):
    system_instruction = (
        "You are a helpful assistant. Answer concisely in 1-2 paragraphs. "
        "Do NOT use step-by-step reasoning, numbered steps, bullet points, "
        "markdown headers, or boxed answers. Just give the direct answer."
    )

    chat_messages = [{"role": "system", "content": system_instruction}] + messages

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "messages": chat_messages,
        "temperature": 0.2,
        "max_tokens": 4096,
        "top_p": 0.9,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stream": True,
    }

    sys.stdout.write(f"SENDING {len(chat_messages)} messages to llama.cpp\n")
    sys.stdout.flush()

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", LLAMA_URL, json=payload) as resp:
            # Send an early heartbeat to prevent idle timeout
            yield ": heartbeat\n\n"

            async for chunk in resp.aiter_text():
                if chunk:
                    yield chunk


# -----------------------------
# RAG endpoint (streaming)
# -----------------------------
@app.get("/ask")
async def ask(q: str, session_id: str = "default"):
    sys.stdout.write("=== RAG /ask HIT ===\n")
    sys.stdout.flush()

    if session_id not in conversations:
        conversations[session_id] = []

    messages = [
        {"role": role, "content": msg}
        for role, msg in conversations[session_id]
    ]

    sys.stdout.write(f"TAVILY CALL: q='{q}'\n")
    sys.stdout.flush()

    snippets = search_web(q)
    context = "\n".join(snippets[:3])
    user_msg = f"{q}\n\n[Web context: {context}]"

    messages.append({"role": "user", "content": user_msg})

    return StreamingResponse(
        ask_llama_stream(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# -----------------------------
# Static frontend
# -----------------------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")