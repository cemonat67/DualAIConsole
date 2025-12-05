import os
from fastapi import FastAPI
from terminal_ws import router as terminal_router, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import requests
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Dual AI Console")
app.include_router(terminal_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # İstersen sonra domain bazlı kısıtlarsın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


@app.get("/")
def root():
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)


@app.post("/api/chat/claude")
async def chat_claude(
    prompt: str = Form(...),
    model: str = Form("claude-sonnet-4-5-20250929"),
    max_tokens: int = Form(400),
    files: Optional[List[UploadFile]] = File(None),
):
    if not ANTHROPIC_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "ANTHROPIC_API_KEY tanımlı değil."},
        )

    extra_context = ""
    if files:
        file_names = [f.filename for f in files]
        extra_context = (
            "\n\nAttached files (names only for now): "
            + ", ".join(file_names)
        )

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt + extra_context,
            }
        ],
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        resp.raise_for_status()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Claude API error: {e}"},
        )

    data = resp.json()
    text_chunks = [
        c.get("text", "")
        for c in data.get("content", [])
        if c.get("type") == "text"
    ]
    answer = "\n\n".join(text_chunks)

    return {
        "model": model,
        "answer": answer,
        "usage": data.get("usage", {}),
    }


@app.post("/api/chat/openai")
async def chat_openai(
    prompt: str = Form(...),
    model: str = Form("gpt-4.1-mini"),
    max_tokens: int = Form(400),
    files: Optional[List[UploadFile]] = File(None),
):
    if not OPENAI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "OPENAI_API_KEY tanımlı değil."},
        )

    extra_context = ""
    if files:
        file_names = [f.filename for f in files]
        extra_context = (
            "\n\nAttached files (names only for now): "
            + ", ".join(file_names)
        )

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant working together with another AI (Claude) for Cem's Zero@Ecosystem projects."
            },
            {
                "role": "user",
                "content": prompt + extra_context,
            },
        ],
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        resp.raise_for_status()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"OpenAI API error: {e}"},
        )

    data = resp.json()
    answer = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    return {
        "model": model,
        "answer": answer,
        "usage": usage,
    }