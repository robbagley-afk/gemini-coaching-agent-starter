# 🚀 Gemini Coaching Agent Starter Template

A clean, production-ready, mobile-first generative AI coaching application powered by **Google Gemini** (`gemini-2.5-flash`).

Built with zero external Python dependencies (pure Python standard library), built-in privacy guardrails (PII blocking), sliding-window rate limiting, and an interactive 4-step workflow.

---

## ⚡ Quickstart (Run in 2 Minutes)

### 1. Clone or Copy This Repository
```bash
git clone <your-repo-url>
cd gemini-coaching-agent-starter
```

### 2. Configure Your Gemini API Key
Create a `.env` file (or set the `GEMINI_API_KEY` environment variable):

```bash
cp .env.example .env
```

Open `.env` and paste your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Get a free API key at [Google AI Studio](https://aistudio.google.com/)).*

### 3. Run the App
```bash
python3 app.py
```
Open **[http://localhost:5050](http://localhost:5050)** in your browser!

---

## 🎨 How to Customize for a New Purpose (5-Minute Checklist)

You can transform this starter template into any type of specialized coach (e.g. *Writing Coach*, *Job Interview Prep*, *Course Planning Assistant*, *Leadership Mentor*) by editing 4 files:

### 1. Update the Coach Persona & Prompt (`app.py`)
In `app.py`, update `SYSTEM_PROMPT` and `MODE_CONTEXTS` to teach Gemini your agent's role, tone, and guidance for each step:

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
- **Sliding-Window Rate Limiter**: Automatically caps requests per IP (default: 80 requests/minute) to protect your quota from abuse.
- **Zero Third-Party Packages**: Uses Python's built-in `http.server` and `urllib.request`. No `pip install` issues, virtual environment conflicts, or dependency security vulnerabilities.
- **Safe Fallback**: If offline or if the API key is missing, provides helpful guidance gracefully with `live: false`.

---

## 📱 Mobile-First Features

- **Instant Chat Viewport**: The chat transcript and response are immediately visible at the top of the mobile screen without having to scroll past large hero banners.
- **Compact Segmented Step Bar**: 4-step selector takes only 38px of height for fast one-tap navigation.
- **Responsive Layout**: Adapts gracefully across iPhones, Android devices, tablets, and desktop browsers.

---

## 📄 License
MIT License. Free to use, adapt, and build upon.
