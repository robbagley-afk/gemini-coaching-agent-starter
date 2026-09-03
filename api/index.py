"""
Vercel Serverless Function - AI Coaching Agent
==============================================
Self-contained Python serverless handler for Vercel deployment.
Routes:
  - GET  /api/status, /healthz
  - POST /api/chat
  - POST /api/feedback
"""

import json
import os
import re
import sqlite3
import ssl
import time
import urllib.error
import urllib.request
from collections import defaultdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

LM_STUDIO_URL = os.environ.get(
    "LM_STUDIO_URL", "https://mac-studio-2.tail299fc7.ts.net:8443/v1"
).rstrip("/")
QWEN_MODEL = os.environ.get("MODEL_NAME", "qwen3-vl-30b-a3b-instruct-mlx").strip()
LM_STUDIO_API_KEY = os.environ.get("LM_STUDIO_API_KEY", "").strip()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "50"))
DB_PATH = Path("/tmp") / "feedback.db"

# ==============================================================================
# 2. FEEDBACK STORE (SQLITE + STDOUT)
# ==============================================================================

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    response_id TEXT NOT NULL,
                    mode TEXT,
                    rating TEXT NOT NULL,
                    question TEXT,
                    answer TEXT,
                    comment TEXT,
                    client_ip TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"[DB Init Warning] {e}")

init_db()

def save_feedback(response_id: str, rating: str, comment: str = "", question: str = "", answer: str = "", mode: str = "", client_ip: str = ""):
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    record = {
        "created_at": now,
        "response_id": response_id,
        "mode": mode,
        "rating": rating,
        "question": question,
        "answer": answer,
        "comment": comment,
        "client_ip": client_ip,
    }
    print(f"[FEEDBACK] {json.dumps(record)}", flush=True)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO feedback (created_at, response_id, mode, rating, question, answer, comment, client_ip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, response_id, mode, rating, question, answer, comment, client_ip))
            conn.commit()
    except Exception as e:
        print(f"[Feedback Save Warning] {e}")

# ==============================================================================
# 3. PROMPT & PERSONA
# ==============================================================================

SYSTEM_PROMPT = """You are a helpful, encouraging, and actionable AI Coach for students.
Your goal is to guide the user step-by-step through their goals with clear, constructive feedback.

Core Guidelines:
1. Warm, professional, and directly actionable tone.
2. Structure your replies clearly using concise paragraphs and bullet points.
3. Keep answers focused on career and professional development.
4. When asked for suggestions or examples, give high-impact phrasing students can immediately use."""

MODE_PROMPTS = {
    "step1": "Focus specifically on Step 1 (Discovery & Foundation). Help the student clarify their baseline.",
    "step2": "Focus specifically on Step 2 (Drafting & Crafting). Provide specific examples, wording, and structure.",
    "step3": "Focus specifically on Step 3 (Review & Polish). Offer constructive critique, pointing out strengths and gaps.",
    "step4": "Focus specifically on Step 4 (Action & Execution). Give a concrete checklist for what to do next."
}

# ==============================================================================
# 4. PRIVACY & RATE LIMITING
# ==============================================================================

PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "Social Security numbers"),
    (re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"), "credit card numbers"),
    (re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+", re.IGNORECASE), "passwords"),
]

def check_privacy(text: str):
    for pattern, name in PII_PATTERNS:
        if pattern.search(text):
            return f"For your privacy and safety, please do not include {name} in your messages."
    return None

class SimpleRateLimiter:
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        history = [t for t in self.requests[client_ip] if t > cutoff]
        history.append(now)
        self.requests[client_ip] = history
        return len(history) <= self.max_requests

RATE_LIMITER = SimpleRateLimiter(max_requests=RATE_LIMIT)

# ==============================================================================
# 5. INFERENCE CLIENTS
# ==============================================================================

def call_qwen(messages: list) -> str:
    url = f"{LM_STUDIO_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if LM_STUDIO_API_KEY:
        headers["Authorization"] = f"Bearer {LM_STUDIO_API_KEY}"
    payload = {
        "model": QWEN_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 700,
        "stream": False,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

def call_gemini(messages: list) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        if msg["role"] == "system":
            role = "user"
            text = f"[SYSTEM INSTRUCTIONS: {msg['content']}]"
        else:
            text = msg["content"]
        contents.append({"role": role, "parts": [{"text": text}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No response generated by Gemini.")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()

def static_fallback(message: str, mode: str) -> str:
    return (
        f"Thank you for sharing your question! Here are key recommendations to move forward:\n\n"
        f"• **Clarify Your Message**: Focus on 1–2 specific accomplishments that demonstrate your strengths.\n"
        f"• **Lead with Impact**: Describe what you accomplished, how you did it, and the tangible outcome.\n"
        f"• **Next Step**: Tailor this draft to the specific role or employer you are targeting."
    )

def ask_coach(user_message: str, mode: str, conversation_history: list = None):
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{MODE_PROMPTS.get(mode, '')}"}]
    if conversation_history:
        for turn in conversation_history[-6:]:
            if "role" in turn and "content" in turn:
                messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    # Tier 1: LM Studio Qwen (Primary)
    try:
        reply = call_qwen(messages)
        if reply:
            return reply, "qwen", True
    except Exception as qwen_err:
        print(f"[Qwen Offline] {qwen_err}")

    # Tier 2: Google Gemini (Fallback)
    if GEMINI_API_KEY:
        try:
            reply = call_gemini(messages)
            if reply:
                return reply, "gemini", True
        except Exception as gemini_err:
            print(f"[Gemini Error] {gemini_err}")

    # Tier 3: Static Guidance
    return static_fallback(user_message, mode), "static", False

# ==============================================================================
# 6. SERVERLESS HTTP HANDLER
# ==============================================================================

class handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/healthz", "/api/status"):
            self._json({
                "status": "ok",
                "service": "AI Coach (Vercel Serverless)",
                "primary_engine": "LM Studio Qwen",
                "primary_model": QWEN_MODEL,
                "fallback_engine": "Google Gemini" if GEMINI_API_KEY else "Static Fallback",
                "fallback_configured": bool(GEMINI_API_KEY),
                "fallback_model": GEMINI_MODEL,
                "rate_limit_per_min": RATE_LIMIT,
            })
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self):
        path = self.path.split("?")[0]

        # ----------------------------------------------------------------------
        # Feedback Submission Endpoint
        # ----------------------------------------------------------------------
        if path == "/api/feedback":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(raw_body)
            except Exception:
                self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
                return

            response_id = str(data.get("response_id", "")).strip()
            rating = str(data.get("rating", "")).strip().lower()
            comment = str(data.get("comment", "")).strip()
            question = str(data.get("question", "")).strip()
            answer = str(data.get("answer", "")).strip()
            mode = str(data.get("mode", "")).strip()

            if rating not in ("up", "down"):
                self._json({"error": "Rating must be 'up' or 'down'."}, HTTPStatus.BAD_REQUEST)
                return

            if comment:
                warning = check_privacy(comment)
                if warning:
                    self._json({"error": warning}, HTTPStatus.BAD_REQUEST)
                    return

            client_ip = self.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
            save_feedback(response_id, rating, comment, question, answer, mode, client_ip)
            self._json({"status": "ok", "message": "Feedback saved."})
            return

        # ----------------------------------------------------------------------
        # Chat Generation Endpoint
        # ----------------------------------------------------------------------
        if path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found.")
            return

        client_ip = self.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
        if not RATE_LIMITER.is_allowed(client_ip):
            self._json(
                {"error": f"Rate limit of {RATE_LIMIT} req/min exceeded. Please wait a moment before sending another message."},
                HTTPStatus.TOO_MANY_REQUESTS,
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_body)
        except Exception:
            self._json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
            return

        message = str(data.get("message", "")).strip()
        mode = str(data.get("mode", "step1")).strip()
        history = data.get("history", [])

        if not message:
            self._json({"error": "Message is required."}, HTTPStatus.BAD_REQUEST)
            return

        privacy_warning = check_privacy(message)
        if privacy_warning:
            self._json({"error": privacy_warning}, HTTPStatus.BAD_REQUEST)
            return

        reply, engine_used, is_live = ask_coach(message, mode, history)
        self._json({
            "reply": reply,
            "engine": engine_used,
            "live": is_live,
            "mode": mode,
            "model": GEMINI_MODEL if engine_used == "gemini" else QWEN_MODEL
        })
