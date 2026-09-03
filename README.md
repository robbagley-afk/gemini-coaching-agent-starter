# 🚀 AI Coaching Agent Starter Template (Dual-Engine: Qwen + Gemini Fallback)

A clean, production-ready, mobile-first generative AI coaching application with a **dual-tier inference engine**:
1. **Primary**: **Qwen** (`qwen3-vl-30b-a3b-instruct-mlx`) hosted on **LM Studio** via a public Tailscale tunnel (zero cost, zero setup).
2. **Fallback**: **Google Gemini** (`gemini-2.5-flash`) used automatically if the local model is offline or unreachable.
3. **Offline**: Safe structured coaching responses if both AI models are unavailable.

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

*(By default, the app is configured to connect to `https://mac-studio-2.tail299fc7.ts.net:8443/v1` for live Qwen inference at zero cost -- see "Getting Access to Tier 1 (Qwen)" below, since this endpoint requires a key).*

---

## 🔑 Getting Access to Tier 1 (Qwen)

The public LM Studio endpoint (`mac-studio-2.tail299fc7.ts.net:8443`) is **not open access** -- it requires an API key, rate-limited per key. Without one, requests to it return `401` and the app automatically falls back to Tier 2 (Gemini) or Tier 3 (offline guidance), so the app still works, just without free local inference.

**Option A -- Request a key (recommended if you want free Qwen inference):**
Email **robbagley@ensign.edu** with your name and intended use. You'll get back a key to set as `LM_STUDIO_API_KEY` in your `.env` file (see `.env.example`).

**Option B -- Generate your own Google Gemini key (fastest, no waiting):**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey) and sign in with a Google account.
2. Click "Create API key" -- the free tier requires no credit card.
3. Paste it into your `.env` file as `GEMINI_API_KEY`.
4. The app will use Gemini automatically whenever Qwen is unavailable or unconfigured.

**Option C -- Run your own local model:**
If you have LM Studio (or any OpenAI-compatible server) running locally, point `LM_STUDIO_URL` at it (e.g. `http://127.0.0.1:1234/v1`) and leave `LM_STUDIO_API_KEY` blank.

---

## 🔄 Dual-Tier Inference Architecture

| Tier | Engine | Target | Description |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Primary)** | **LM Studio Qwen** | `https://mac-studio-2.tail299fc7.ts.net:8443/v1` | Fast, token-free, private local inference. |
| **Tier 2 (Fallback)** | **Google Gemini** | `gemini-2.5-flash` | Cloud fallback if LM Studio is restarting or offline. (Set `GEMINI_API_KEY` in `.env`). |
| **Tier 3 (Offline)** | **Structured Fallback** | Local Python engine | Helpful guidance guaranteed even without internet. |

To configure the optional Gemini fallback, copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
And add your free Gemini key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🎨 How to Customize for a New Purpose (5-Minute Checklist)

You can transform this starter template into any type of specialized coach (e.g. *Writing Coach*, *Job Interview Prep*, *Course Planning Assistant*, *Leadership Mentor*) by editing 4 files:

### 1. Update the Coach Persona & Prompt (`app.py`)
In `app.py`, update `SYSTEM_PROMPT` and `MODE_CONTEXTS` to teach the coach its role, tone, and guidance for each step:

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

- **Default Rate Limiter**: Configured to **50 requests/minute per IP** (customizable via `RATE_LIMIT_PER_MIN`).
- **PII Guardrail**: Regex filters automatically reject Social Security numbers, credit card numbers, and passwords before any text is sent to the AI model.
- **Zero Third-Party Packages**: Uses Python's built-in `http.server` and `urllib.request`. No `pip install` issues, virtual environment conflicts, or dependency vulnerabilities.

---

## 📱 Mobile-First Features

- **Instant Chat Viewport**: The chat transcript and response are immediately visible at the top of the mobile screen without having to scroll past large hero banners.
- **Compact Segmented Step Bar**: 4-step selector takes only 38px of height for fast one-tap navigation.
---

## 🌐 Deploy to Vercel (Free 24/7 Cloud Hosting)

This repository includes native Vercel serverless configuration (`vercel.json` and `api/index.py`).

1. Go to [Vercel](https://vercel.com) and sign in with GitHub.
2. Click **Add New...** → **Project**.
3. Import your repository (`gemini-coaching-agent-starter` or your fork).
4. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(your Google AI Studio key)*
   - `GEMINI_MODEL`: `gemini-2.5-flash` (default)
5. Click **Deploy**.

> **Result**: Your app is live with a global CDN URL (e.g. `https://your-coach-app.vercel.app`), zero cold starts, automatic HTTPS, and automatic updates whenever you push commits to GitHub!

---

## 📄 License
MIT License. Free to use, adapt, and build upon.
