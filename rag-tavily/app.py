from fastapi import FastAPI
import requests
import os
from typing import List, Dict
from fastapi.staticfiles import StaticFiles
import sys
import json

app = FastAPI()

LLAMA_URL = os.getenv("LLAMA_URL", "http://llama-cpp.llama-cpp.svc.cluster.local:8080/v1/chat/completions")

# In-memory conversation store
conversations: Dict[str, List[tuple]] = {}

def search_web(query: str):
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return ["No TAVILY_API_KEY - using mock context"]
    
    r = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "query": query,
            "search_depth": "basic",
            "max_results": 3
        }
    )
    
    if r.status_code != 200:
        return [f"Search API error: {r.status_code}"]
    
    data = r.json()
    return [item.get("content", "") for item in data.get("results", [])]

def ask_llama(messages: list):
    sys.stdout.write("=== LLAMA API START ===\n")
    sys.stdout.flush()
    
    try:
        url = LLAMA_URL
        
        sys.stdout.write(f"SENDING to: {url}\n")
        sys.stdout.flush()
        
        # For CHAT endpoint - build proper messages array
        system_instruction = """You are a helpful assistant. Answer concisely in 1-2 paragraphs. 
Do NOT use step-by-step reasoning, numbered steps, bullet points, markdown headers, or boxed answers. 
Just give the direct answer."""
        
        chat_messages = [
            {"role": "system", "content": system_instruction}
        ] + messages
        
        sys.stdout.write(f"SENDING {len(chat_messages)} messages\n")
        sys.stdout.flush()
        
        r = requests.post(
            url,
            json={
                "model": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "messages": chat_messages,
                "temperature": 0.2,
                "max_tokens": 4096,
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "stream": True
            },
            timeout=180
        )
        
        sys.stdout.write(f"STATUS: {r.status_code}\n")
        sys.stdout.write(f"RAW RESPONSE: {r.text[:500]}...\n")
        sys.stdout.flush()
        
        data = r.json()
        sys.stdout.write(f"TOP LEVEL KEYS: {list(data.keys())}\n")
        if "choices" in data and data["choices"]:
            sys.stdout.write(f"CHOICES[0] KEYS: {list(data['choices'][0].keys())}\n")
        sys.stdout.flush()
        
        # Try both possible paths with detailed error info
        try:
            content = data["choices"][0]["text"]
            sys.stdout.write(f"Found 'text' field\n")
        except KeyError:
            try:
                content = data["choices"][0]["message"]["content"]
                sys.stdout.write(f"Found 'message.content' field\n")
            except KeyError as e2:
                sys.stdout.write(f"Available CHOICES[0] keys: {list(data['choices'][0].keys())}\n")
                raise Exception(f"Neither path works. CHOICES[0] keys: {list(data['choices'][0].keys())}")
        
        sys.stdout.write(f"SUCCESS: {len(content)} chars\n")
        sys.stdout.flush()
        return content
        
    except Exception as e:
        sys.stdout.write(f"ERROR: {str(e)}\n")
        sys.stdout.flush()
        return f"LLM error: {str(e)}"

@app.get("/ask")
def ask(q: str, session_id: str = "default"):
    sys.stdout.write("=== RAG /ask HIT ===\n")
    sys.stdout.flush()
    
    try:
        if session_id not in conversations:
            conversations[session_id] = []
        
        messages = [{"role": role, "content": msg} for role, msg in conversations[session_id]]
        
        sys.stdout.write(f"TAVILY CALL: q='{q}'\n")
        sys.stdout.flush()
        
        snippets = search_web(q)
        sys.stdout.write(f"TAVILY RESULT: {len(snippets)} snippets\n")
        sys.stdout.flush()
        
        if snippets:
            sys.stdout.write(f"FIRST SNIPPET: {snippets[0][:100]}\n")
            sys.stdout.flush()
        
        # FIXED: Real newlines (not escaped)
        context = "\n".join(snippets[:3])
        user_msg = f"{q}\n\n[Web context: {context}]"
        
        sys.stdout.write(f"PROMPT TO LLAMA: {user_msg[:150]}...\n")
        sys.stdout.flush()
        
        messages.append({"role": "user", "content": user_msg})
        answer = ask_llama(messages)
        
        sys.stdout.write(f"LLAMA RESPONSE: {answer[:100]}...\n")
        sys.stdout.flush()
        
        conversations[session_id].extend([("user", user_msg), ("assistant", answer)])
        return {"answer": answer}
    
    except Exception as e:
        sys.stdout.write(f"ERROR: {str(e)}\n")
        sys.stdout.flush()
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")