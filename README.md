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

*(By default, the app immediately connects to `https://mac-studio-2.tail299fc7.ts.net:8443/v1` for live Qwen inference at zero cost).*

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
- **Responsive Layout**: Adapts gracefully across iPhones, Android devices, tablets, and desktop browsers.

---

## 📄 License
MIT License. Free to use, adapt, and build upon.
