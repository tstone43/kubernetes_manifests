from fastapi import FastAPI
import requests
import os

app = FastAPI()

# URL of your llama.cpp server inside K3s
LLAMA_URL = "http://llama-cpp.llama-cpp.svc.cluster.local:8080/completion"

# LangSearch has no API key requirement
LANGSEARCH_URL = "https://api.langsearch.ai/search"


def search_web(query: str):
    """Call LangSearch and return a list of snippet strings."""
    r = requests.get(
        LANGSEARCH_URL,
        params={"q": query}
    )
    data = r.json()

    # LangSearch returns: { "results": [ { "snippet": "...", ... }, ... ] }
    return [item.get("snippet", "") for item in data.get("results", [])]


def ask_llama(prompt: str):
    """Send the constructed prompt to llama.cpp."""
    r = requests.post(
        LLAMA_URL,
        json={
            "prompt": prompt,
            "temperature": 0.2,
            "max_tokens": 512
        }
    )
    return r.json()["content"]


@app.get("/ask")
def ask(q: str):
    """Main endpoint: search ? inject ? ask llama.cpp."""
    snippets = search_web(q)
    context = "\n".join(snippets)

    prompt = f"""
You are an assistant with access to current information.
Use ONLY the context below to answer the question.

Context:
{context}

Question: {q}

Answer:
"""

    answer = ask_llama(prompt)
    return {"answer": answer}