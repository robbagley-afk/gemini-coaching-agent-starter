/**
 * Gemini Coaching Agent - Frontend Logic
 * ---------------------------------------
 * Configure your 4 step modes, opening greetings, and starter prompts below!
 */

const MODES = {
  step1: {
    label: 'Discovery & Research',
    opener: 'Welcome! Tell me about the goal, role, or topic you want to explore today. We’ll identify key requirements and a strong opening strategy.',
    prompts: [
      'Help me research key skills for a new role.',
      'What should I prioritize when exploring this opportunity?'
    ]
  },
  step2: {
    label: 'Drafting & Core Message',
    opener: 'Let’s build your core message or introduction. Share your background, one concrete proof point or story, and your target audience.',
    prompts: [
      'Help me draft a concise 30-second introduction.',
      'Here is my rough draft. Help me make it clearer and more impactful.'
    ]
  },
  step3: {
    label: 'Practice & Feedback',
    opener: 'I’ll role-play as your reviewer or interviewer. Share your response, and I’ll ask realistic follow-ups and offer practical coaching.',
    prompts: [
      'Let’s do a practice scenario. Start with a common question.',
      'Give me feedback on how I can explain my experience with real impact.'
    ]
  },
  step4: {
    label: 'Preparation & Strategic Questions',
    opener: 'Let’s prepare questions that show genuine curiosity, research, and insight. What specific organization or team are you meeting with?',
    prompts: [
      'Give me 2 thoughtful questions about team culture and growth.',
      'How do I ask about project ownership without sounding demanding?'
    ]
  },
};

let currentMode = 'step1';
let chatHistory = [];

// DOM Elements
const messagesEl = document.querySelector('#messages');
const suggestionsEl = document.querySelector('#suggestions');
const inputEl = document.querySelector('#message-input');
const formEl = document.querySelector('#chat-form');
const modeLabelEl = document.querySelector('#mode-label');
const statusEl = document.querySelector('#service-status');
const newChatBtn = document.querySelector('#new-chat');

/**
 * Appends a message bubble to the transcript and smoothly scrolls to it
 */
function addMessage(role, text) {
  const item = document.createElement('article');
  item.className = `message ${role}`;
  item.innerHTML = `<small>${role === 'assistant' ? 'AI Coach' : 'You'}</small>`;
  
  const content = document.createElement('div');
  content.textContent = text;
  item.appendChild(content);
  messagesEl.appendChild(item);

  // Smooth scroll
  requestAnimationFrame(() => {
    messagesEl.scrollTop = messagesEl.scrollHeight;
    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

/**
 * Switches the active mode / step
 */
function setMode(modeKey) {
  if (!MODES[modeKey]) return;
  currentMode = modeKey;

  // Update mode label
  if (modeLabelEl) {
    modeLabelEl.textContent = MODES[currentMode].label;
  }

  // Update button active states
  document.querySelectorAll('.step-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.mode === currentMode);
  });

  // Reset conversation for new step
  messagesEl.innerHTML = '';
  chatHistory = [];

  // Post coach opener
  addMessage('assistant', MODES[currentMode].opener);

  // Render clickable prompt suggestions
  suggestionsEl.innerHTML = '';
  MODES[currentMode].prompts.forEach((promptText) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = promptText;
    btn.addEventListener('click', () => {
      inputEl.value = promptText;
      inputEl.focus();
      autoGrowInput();
    });
    suggestionsEl.appendChild(btn);
  });
}

/**
 * Sends a message to the backend and renders the response
 */
async function submitMessage(message) {
  addMessage('user', message);
  chatHistory.push({ role: 'user', content: message });
  statusEl.textContent = 'Thinking…';

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        mode: currentMode,
        history: chatHistory
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Something went wrong.');
    }

    addMessage('assistant', data.reply);
    chatHistory.push({ role: 'assistant', content: data.reply });
    statusEl.textContent = data.live ? 'AI Live' : 'Helpful fallback';
  } catch (err) {
    addMessage('assistant', err.message || 'I encountered an error. Please try again.');
    statusEl.textContent = 'Try again';
  }
}

function autoGrowInput() {
  inputEl.style.height = '44px';
  if (inputEl.scrollHeight > 44) {
    inputEl.style.height = `${Math.min(inputEl.scrollHeight, 90)}px`;
  }
}

// Event Listeners
formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const msg = inputEl.value.trim();
  if (!msg) return;
  inputEl.value = '';
  inputEl.style.height = '44px';
  await submitMessage(msg);
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    formEl.dispatchEvent(new Event('submit', { cancelable: true }));
  }
});

inputEl.addEventListener('input', autoGrowInput);

document.querySelectorAll('.step-btn').forEach((btn) => {
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
});

if (newChatBtn) {
  newChatBtn.addEventListener('click', () => setMode(currentMode));
}

// Initialize default mode
setMode(currentMode);
