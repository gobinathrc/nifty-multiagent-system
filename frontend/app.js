/**
 * Nifty Multi-Agent Frontend Controller.
 * Handles user interactions, message rendering, and mock/API response dispatching.
 */

const chatViewport = document.getElementById('chatViewport');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');

/**
 * Appends a bubble to the chat viewport.
 * @param {string} text - Message content.
 * @param {'user' | 'bot' | 'system'} sender - Message origin.
 */
function appendMessage(text, sender) {
  const msgWrapper = document.createElement('div');
  msgWrapper.classList.add('message', `${sender}-message`);

  const content = document.createElement('div');
  content.classList.add('message-content');
  content.textContent = text;

  msgWrapper.appendChild(content);
  chatViewport.appendChild(msgWrapper);
  chatViewport.scrollTop = chatViewport.scrollHeight;
}

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const query = userInput.value.trim();
  if (!query) return;

  // Append user message
  appendMessage(query, 'user');
  userInput.value = '';

  // Simulate routing indicator
  const pendingBot = document.createElement('div');
  pendingBot.classList.add('message', 'bot-message');
  pendingBot.innerHTML = '<div class="message-content"><em>Routing to agent & checking cache...</em></div>';
  chatViewport.appendChild(pendingBot);
  chatViewport.scrollTop = chatViewport.scrollHeight;

  // Dispatch to backend API (or simulated local response if offline)
  setTimeout(() => {
    pendingBot.remove();
    let reply = "";
    const lower = query.toLowerCase();

    if (lower.includes("price") || lower.includes("live")) {
      reply = "[Agent A - Live Quote]\nNifty 50: ₹24,850.20 (+0.45% today). Status: Strong intraday support.";
    } else if (lower.includes("chart") || lower.includes("trend") || lower.includes("plot")) {
      reply = "[Agent B - Visual Chart Vision]\n1. Trend: Consistent Uptrend\n2. Key Levels: Support at ₹24,600, Resistance at ₹25,100\n3. Visual Pattern: Higher-high consolidation.";
    } else if (lower.includes("book") || lower.includes("rule") || lower.includes("murphy")) {
      reply = "[Agent C - Book Theory (Murphy)]\n- Rule: Never buy directly into resistance.\n- Confirmation: Wait for a high-volume breakout before executing.";
    } else {
      reply = `[SQL Dynamic Query]\nFetched 7-day data from SQLite table 'nifty_ohlcv'. Average price: ₹24,780.00.`;
    }

    appendMessage(reply, 'bot');
  }, 600);
});
