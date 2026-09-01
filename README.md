# 🚀 AI Coaching Agent Starter Template (LM Studio Qwen Powered)

A clean, production-ready, mobile-first generative AI coaching application powered by **Qwen** (`qwen3-vl-30b-a3b-instruct-mlx`) running on **LM Studio** via a dedicated **public Tailscale tunnel**.

**Zero cloud API keys required!** Any application cloned or built from this starter template automatically connects to the shared Mac Studio local LLM inference stack.

---

## ⚡ Quickstart (Run in 1 Minute)

### 1. Clone This Repository
```bash
git clone https://github.com/robbagley-afk/gemini-coaching-agent-starter.git my-coach-app
cd my-coach-app
```

### 2. Run the App
```bash
python3 app.py
```
Open **[http://localhost:5050](http://localhost:5050)** in your browser!

*(The app immediately connects to `https://mac-studio-2.tail299fc7.ts.net:8443/v1` for live Qwen inference at zero cost).*

---

## 🌐 Public Tailscale Inference Tunnel

The app connects to the shared LM Studio OpenAI-compatible endpoint:

- **Public Tailscale Tunnel Endpoint**: `https://mac-studio-2.tail299fc7.ts.net:8443/v1`
- **Tailnet Internal Endpoint**: `https://mac-studio-2.tail299fc7.ts.net:1234/v1`
- **Mac Studio Local Loopback**: `http://127.0.0.1:1234/v1`
- **Active Model**: `qwen3-vl-30b-a3b-instruct-mlx`

If running on a different machine or port, create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

---

## 🎨 How to Customize for a New Purpose (5-Minute Checklist)

You can transform this starter template into any type of specialized coach (e.g. *Writing Coach*, *Job Interview Prep*, *Course Planning Assistant*, *Leadership Mentor*) by editing 4 files:

### 1. Update the Coach Persona & Prompt (`app.py`)
In `app.py`, update `SYSTEM_PROMPT` and `MODE_CONTEXTS` to teach Qwen your agent's role, tone, and guidance for each step:

```python
SYSTEM_PROMPT = """You are [New Coach Name]. Your goal is to guide the user in [Topic]..."""

MODE_CONTEXTS = {
    "step1": "Mode: Step 1 (Discovery & Needs Analysis)...",
    "step2": "Mode: Step 2 (Drafting & Idea Formation)...",
    "step3": "Mode: Step 3 (Interactive Practice & Feedback)...",
    "step4": "Mode: Step 4 (Preparation & Next Steps)...",
}
```

### 2. Configure the 4 Steps & Clickable Starter Prompts (`static/app.js`)
In `static/app.js`, edit `MODES` with the step names, opening greetings, and clickable prompt buttons:

```javascript
const MODES = {
  step1: {
    label: 'Discovery & Research',
    opener: 'Welcome! What goal would you like to explore today?',
    prompts: [
      'Help me research key skills for a new role.',
      'What should I prioritize when exploring this opportunity?'
    ]
  },
  // step2, step3, step4...
};
```

### 3. Change Brand Title & Step Labels (`static/index.html`)
In `static/index.html`:
- Update `<title>` and `<a class="brand">` with your app title.
- Update the text inside `<button class="step-btn">` to match your 4 step names.

### 4. Customize Brand Colors (`static/styles.css`)
In `static/styles.css`, change the 3 CSS variables at the top to match your department or organization's branding:

```css
:root {
  --primary: #1e3a8a;        /* Main brand color (header & buttons) */
  --primary-deep: #0f172a;   /* Dark background gradient */
  --accent-gold: #f59e0b;    /* Highlight accent & step badges */
}
```

---

## 🛡️ Built-In Privacy & Security Guardrails

- **PII Guardrail**: Regex filters automatically reject Social Security numbers, credit card numbers, and passwords before any text is sent to the AI model.
- **Sliding-Window Rate Limiter**: Automatically caps requests per IP (default: 80 requests/minute) to protect the shared server from abuse.
- **Zero Third-Party Packages**: Uses Python's built-in `http.server` and `urllib.request`. No `pip install` issues, virtual environment conflicts, or dependency security vulnerabilities.
- **Safe Fallback**: If offline or if the inference server is restarting, provides helpful guidance gracefully with `live: false`.

---

## 📱 Mobile-First Features

- **Instant Chat Viewport**: The chat transcript and response are immediately visible at the top of the mobile screen without having to scroll past large hero banners.
- **Compact Segmented Step Bar**: 4-step selector takes only 38px of height for fast one-tap navigation.
- **Responsive Layout**: Adapts gracefully across iPhones, Android devices, tablets, and desktop browsers.

---

## 📄 License
MIT License. Free to use, adapt, and build upon.
