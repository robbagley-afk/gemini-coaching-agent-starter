#!/usr/bin/env python3
"""
LM Studio Qwen Coaching Agent Starter Template
----------------------------------------------
A lightweight, zero-dependency Python backend for a multi-step generative AI coach
powered by Qwen (qwen3-vl-30b-a3b-instruct-mlx) on LM Studio via a public Tailscale tunnel.

Features:
- Pure Python standard library (no pip install required)
- Uses shared LM Studio Qwen endpoint (no API key needed!)
- Built-in Privacy / PII filters (blocks SSNs, credit cards, passwords)
- Per-IP sliding window rate limiting
- Multi-step workflow context routing
- Safe fallback responses when offline
"""

import json
import os
import re
import ssl
import time
from collections import defaultdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

# Load .env file manually if present (no external packages needed)
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Public Tailscale Funnel endpoint for Mac Studio LM Studio (or local loopback http://127.0.0.1:1234/v1)
LM_STUDIO_URL = os.environ.get(
    "LM_STUDIO_URL",
    "https://mac-studio-2.tail299fc7.ts.net:8443/v1"
).rstrip("/")

MODEL = os.environ.get("MODEL_NAME", "qwen3-vl-30b-a3b-instruct-mlx").strip()
PORT = int(os.environ.get("PORT", "5050"))
HOST = os.environ.get("HOST", "0.0.0.0")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "80"))

STATIC_DIR = Path(__file__).resolve().parent / "static"

# ==============================================================================
# 2. COACH SYSTEM PROMPT & PERSONA
# ==============================================================================
# Customize this prompt for your agent's specific focus and purpose!

SYSTEM_PROMPT = """You are a helpful, encouraging, and actionable AI Coach for students.
Your goal is to guide the user step-by-step through their goals with clear, constructive feedback.

Core Guidelines:
1. Be concise, warm, and conversational.
2. Ask only ONE focused follow-up question at a time to avoid overwhelming the user.
3. Preserve the user's authentic voice when refining their ideas or drafts.
4. Give specific praise for what works, and clear suggestions for improvement.
5. If the user asks for help brainstorming, give 2-3 distinct, realistic ideas.
"""

# Contextual instructions prepended based on which step the user is on
MODE_CONTEXTS = {
    "step1": "Mode: Step 1 (Discovery & Research). Help the user explore ideas, analyze key requirements, and clarify their target direction.",
    "step2": "Mode: Step 2 (Drafting & Core Message). Guide the user in building a compelling, clear message or draft. Highlight proof points.",
    "step3": "Mode: Step 3 (Practice & Role-Play). Act as a realistic partner/reviewer. Give realistic responses and ask one relevant follow-up at a time.",
    "step4": "Mode: Step 4 (Preparation & Strategic Questions). Help the user craft thoughtful, high-impact questions to ask in their upcoming opportunity.",
}

# ==============================================================================
# 3. PRIVACY FILTER & GUARDRAILS
# ==============================================================================

PII_PATTERNS = [
    # Social Security Numbers (e.g., 000-00-0000 or 000 00 0000)
    (re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"), "Social Security numbers"),
    # Credit Card Numbers (13 to 19 digits with dashes or spaces)
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{1,4}\b"), "payment card numbers"),
    # Password disclosures
    (re.compile(r"\b(?:password|pwd|passcode|secret_key)\s*[:=]\s*\S+", re.IGNORECASE), "passwords"),
]

def check_privacy(text: str) -> str | None:
    """Returns a warning message if sensitive PII is detected, else None."""
    for pattern, label in PII_PATTERNS:
        if pattern.search(text):
            return f"For your privacy and safety, please remove {label} or private identifiers before submitting."
    return None

# ==============================================================================
# 4. SLIDING-WINDOW RATE LIMITER
# ==============================================================================

class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int = 80):
        self.limit = limit_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        # Prune older timestamps
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        if len(self.requests[client_ip]) >= self.limit:
            return False
        self.requests[client_ip].append(now)
        return True

RATE_LIMITER = SlidingWindowRateLimiter(limit_per_minute=RATE_LIMIT)

# ==============================================================================
# 5. LM STUDIO QWEN INFERENCE & FALLBACK ENGINE
# ==============================================================================

def fallback_reply(message: str, mode: str) -> str:
    """Safe fallback response if LM Studio is offline or unreachable."""
    fallbacks = {
        "step1": "Great start exploring this topic! Tell me more about what specific goal or organization you want to target.",
        "step2": "Let's work on your message. Share your main goal, one clear proof point or example, and what makes you unique.",
        "step3": "I'm ready to practice with you! Share your draft response and I will provide feedback and a realistic follow-up.",
        "step4": "Here is a strong starter question: 'What qualities help someone succeed most in this role?' How would you like to customize it?",
    }
    return fallbacks.get(mode, "Thanks for sharing! What specific aspect would you like to work on next?")


def ask_qwen(message: str, mode: str, history: list[dict[str, str]]) -> tuple[str, bool]:
    """
    Calls LM Studio OpenAI-compatible /v1/chat/completions endpoint.
    Returns (reply_text, is_live_ai_boolean).
    """
    mode_context = MODE_CONTEXTS.get(mode, "")
    system_content = f"{SYSTEM_PROMPT}\n\n{mode_context}".strip()

    messages = [{"role": "system", "content": system_content}]

    # Include recent multi-turn history
    for item in history[-8:]:
        role = item.get("role", "user")
        content = str(item.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1024,
    }

    url = f"{LM_STUDIO_URL}/chat/completions"
    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }

    request = Request(url, data=req_data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=45, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        choices = data.get("choices", [])
        if not choices:
            return fallback_reply(message, mode), False

        reply_text = choices[0].get("message", {}).get("content", "").strip()
        if not reply_text:
            return fallback_reply(message, mode), False

        return reply_text, True
    except (URLError, HTTPError, TimeoutError, ValueError, KeyError, OSError) as e:
        print(f"[LM Studio Inference Error] {e}")
        return fallback_reply(message, mode), False


# ==============================================================================
# 6. HTTP REQUEST HANDLER
# ==============================================================================

class CoachHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _json(self, payload: dict, status: int = HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Health & status endpoints
        if self.path in ("/healthz", "/api/status"):
            self._json({
                "status": "ok",
                "service": "AI Coach",
                "engine": "LM Studio Qwen",
                "model": MODEL,
                "endpoint": LM_STUDIO_URL,
                "rate_limit_per_min": RATE_LIMIT,
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        # 1. Rate Limiting Check
        client_ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        if not RATE_LIMITER.is_allowed(client_ip):
            self._json(
                {"error": "Rate limit exceeded. Please wait a moment before sending another message."},
                HTTPStatus.TOO_MANY_REQUESTS,
            )
            return

        # 2. Parse JSON body
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

        # 3. Privacy Guardrail Check
        privacy_warning = check_privacy(message)
        if privacy_warning:
            self._json({"error": privacy_warning}, HTTPStatus.BAD_REQUEST)
            return

        # 4. Generate Coach Response via Qwen
        reply, is_live = ask_qwen(message, mode, history)
        self._json({"reply": reply, "live": is_live})


# ==============================================================================
# 7. SERVER ENTRYPOINT
# ==============================================================================

def main():
    server_address = (HOST, PORT)
    with ThreadingHTTPServer(server_address, CoachHandler) as httpd:
        print("================================================================")
        print(f"🚀 AI Coach Starter running at http://localhost:{PORT}")
        print(f"   Inference Engine: LM Studio ({MODEL})")
        print(f"   Endpoint:         {LM_STUDIO_URL}")
        print("================================================================")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    main()
