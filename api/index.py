"""
Vercel Serverless Function Handler
----------------------------------
Serves /api/chat, /api/feedback, /api/status, and /healthz.
Static assets are served directly from /public by Vercel Edge CDN.
"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path so app module can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app

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
                "primary_model": app.QWEN_MODEL,
                "fallback_engine": "Google Gemini" if app.GEMINI_API_KEY else "Static Fallback",
                "fallback_configured": bool(app.GEMINI_API_KEY),
                "fallback_model": app.GEMINI_MODEL,
                "rate_limit_per_min": app.RATE_LIMIT,
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
                warning = app.check_privacy(comment)
                if warning:
                    self._json({"error": warning}, HTTPStatus.BAD_REQUEST)
                    return

            client_ip = self.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
            try:
                app.save_feedback(response_id, rating, comment, question, answer, mode, client_ip)
                self._json({"status": "ok", "message": "Feedback saved."})
            except Exception as e:
                print(f"[Feedback Save Error] {e}")
                self._json({"error": "Failed to save feedback."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # ----------------------------------------------------------------------
        # Chat Generation Endpoint
        # ----------------------------------------------------------------------
        if path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found.")
            return

        client_ip = self.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
        if not app.RATE_LIMITER.is_allowed(client_ip):
            self._json(
                {"error": f"Rate limit of {app.RATE_LIMIT} req/min exceeded. Please wait a moment before sending another message."},
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

        privacy_warning = app.check_privacy(message)
        if privacy_warning:
            self._json({"error": privacy_warning}, HTTPStatus.BAD_REQUEST)
            return

        reply, engine_used, is_live = app.ask_coach(message, mode, history)
        self._json({
            "reply": reply,
            "engine": engine_used,
            "live": is_live,
            "mode": mode,
            "model": app.GEMINI_MODEL if engine_used == "gemini" else app.QWEN_MODEL
        })
