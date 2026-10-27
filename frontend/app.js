/**
 * Nifty Multi-Agent Frontend Controller.
 * Handles user interactions, message rendering with Markdown support, and real API dispatching.
 */

const chatViewport = document.getElementById('chatViewport');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');

/**
 * Appends a bubble to the chat viewport.
 * Uses marked.js to render bold text, bullet points, and headers cleanly.
 * @param {string} text - Message content.
 * @param {'user' | 'bot' | 'system'} sender - Message origin.
 */
function appendMessage(text, sender) {
  const msgWrapper = document.createElement('div');
  msgWrapper.classList.add('message', `${sender}-message`);

  const content = document.createElement('div');
  content.classList.add('message-content');

  if (sender === 'bot' && window.marked) {
    // Parse markdown into clean HTML (removes raw ### and ***)
    content.innerHTML = marked.parse(text);
  } else {
    content.textContent = text;
  }

  msgWrapper.appendChild(content);
  chatViewport.appendChild(msgWrapper);
  chatViewport.scrollTop = chatViewport.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = userInput.value.trim();
  if (!query) return;

  // Append user message
  appendMessage(query, 'user');
  userInput.value = '';

  // Show routing indicator
  const pendingBot = document.createElement('div');
  pendingBot.classList.add('message', 'bot-message');
  pendingBot.innerHTML = '<div class="message-content"><em>Analyzing real-time market data, news & chart trend...</em></div>';
  chatViewport.appendChild(pendingBot);
  chatViewport.scrollTop = chatViewport.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query, session_id: 'browser_session_1' })
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    pendingBot.remove();
    appendMessage(data.reply, 'bot');
  } catch (err) {
    pendingBot.remove();
    appendMessage("Error communicating with backend server: " + err.message, 'bot');
  }
});
