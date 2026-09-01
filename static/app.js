/**
 * Dual-Engine AI Coaching Agent - Frontend Logic
 * -----------------------------------------------
 * Handles step modes, multi-turn chat, prompt chips,
 * and thumbs up / thumbs down feedback controls.
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
let lastUserMessage = '';

// DOM Elements
const messagesEl = document.querySelector('#messages');
const suggestionsEl = document.querySelector('#suggestions');
const inputEl = document.querySelector('#message-input');
const formEl = document.querySelector('#chat-form');
const modeLabelEl = document.querySelector('#mode-label');
const statusEl = document.querySelector('#service-status');
const newChatBtn = document.querySelector('#new-chat');

/**
 * Creates a helper button for feedback actions
 */
function createFeedbackButton(label, className) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = `feedback-button ${className}`;
  btn.textContent = label;
  return btn;
}

/**
 * Attaches thumbs up / thumbs down feedback controls to an AI response
 */
function addFeedbackControls(messageArticle, responseId, questionText, answerText) {
  if (!responseId) return;

  const region = document.createElement('div');
  region.className = 'answer-feedback';
  region.setAttribute('aria-label', 'Response feedback');

  const prompt = document.createElement('p');
  prompt.className = 'feedback-prompt';
  prompt.textContent = 'Was this response helpful?';

  const controls = document.createElement('div');
  controls.className = 'feedback-controls';

  const upButton = createFeedbackButton('👍 Helpful', 'feedback-up');
  const downButton = createFeedbackButton('👎 Suggested Improvement', 'feedback-down');
  controls.append(upButton, downButton);

  const form = document.createElement('form');
  form.className = 'feedback-form';
  form.hidden = true;

  const commentLabel = document.createElement('label');
  commentLabel.textContent = 'How can this response be improved?';

  const commentInput = document.createElement('textarea');
  commentInput.rows = 3;
  commentInput.placeholder = 'Explain what was missing, incorrect, or how to phrase it better...';
  commentInput.required = true;

  const warning = document.createElement('p');
  warning.className = 'feedback-warning';
  warning.textContent = '🔒 Keep personal or identifying information out of feedback.';

  const formActions = document.createElement('div');
  formActions.className = 'feedback-form-actions';
  const submitButton = createFeedbackButton('Submit Feedback', 'feedback-submit');
  submitButton.type = 'submit';
  const cancelButton = createFeedbackButton('Cancel', 'feedback-cancel');
  formActions.append(submitButton, cancelButton);

  form.append(commentLabel, commentInput, warning, formActions);

  const status = document.createElement('p');
  status.className = 'feedback-status';

  region.append(prompt, controls, form, status);
  messageArticle.appendChild(region);

  let submitted = false;
  const setDisabled = (val) => {
    upButton.disabled = val;
    downButton.disabled = val;
    submitButton.disabled = val;
    cancelButton.disabled = val;
    commentInput.disabled = val;
  };

  const submitFeedback = async (payload) => {
    setDisabled(true);
    status.textContent = 'Saving feedback…';
    try {
      const resp = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          response_id: responseId,
          mode: currentMode,
          question: questionText,
          answer: answerText,
          ...payload
        })
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to save feedback.');
      }
      submitted = true;
      controls.hidden = true;
      form.hidden = true;
      prompt.hidden = true;
      status.className = 'feedback-status feedback-success';
      status.textContent = payload.rating === 'up'
        ? '✓ Thank you! Marked as helpful.'
        : '✓ Thank you! Your suggestion was saved.';
    } catch (err) {
      status.className = 'feedback-status feedback-error';
      status.textContent = err.message || 'Feedback could not be saved.';
      setDisabled(false);
    }
  };

  upButton.addEventListener('click', () => {
    if (!submitted) submitFeedback({ rating: 'up' });
  });

  downButton.addEventListener('click', () => {
    if (submitted) return;
    form.hidden = false;
    status.textContent = '';
    commentInput.focus();
  });

  cancelButton.addEventListener('click', () => {
    form.hidden = true;
    status.textContent = '';
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!submitted && commentInput.value.trim()) {
      submitFeedback({
        rating: 'down',
        comment: commentInput.value.trim()
      });
    }
  });
}

/**
 * Appends a message bubble to the transcript and smoothly scrolls to it
 */
function addMessage(role, text, responseId = null, questionText = '') {
  const item = document.createElement('article');
  item.className = `message ${role}`;
  item.innerHTML = `<small>${role === 'assistant' ? 'AI Coach' : 'You'}</small>`;
  
  const content = document.createElement('div');
  content.textContent = text;
  item.appendChild(content);

  // Attach feedback controls if this is a live AI reply
  if (role === 'assistant' && responseId) {
    addFeedbackControls(item, responseId, questionText, text);
  }

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
  lastUserMessage = '';

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
  lastUserMessage = message;
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

    addMessage('assistant', data.reply, data.response_id, lastUserMessage);
    chatHistory.push({ role: 'assistant', content: data.reply });

    if (data.live) {
      statusEl.textContent = data.engine === 'gemini' ? 'Gemini Live' : 'Qwen Live';
    } else {
      statusEl.textContent = 'Helpful fallback';
    }
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
