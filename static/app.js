const chat = document.getElementById('chat');
const form = document.getElementById('form');
const input = document.getElementById('input');
const send = document.getElementById('send');

// ---- Theme toggle (remembers choice) ----
const root = document.documentElement;
const toggle = document.getElementById('theme-toggle');
function applyTheme(t){
  root.setAttribute('data-theme', t);
  toggle.textContent = t === 'dark' ? '☀️' : '🌙';
}
let saved = 'light';
try { saved = localStorage.getItem('theme') || 'light'; } catch (e) {}
applyTheme(saved);
toggle.addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('theme', next); } catch (e) {}
  applyTheme(next);
});

// ---- Helpers ----
const add = (html, cls) => {
  const d = document.createElement('div');
  d.className = cls;
  d.innerHTML = html;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
};
const esc = s => (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// Pause other previews when one starts (single-track playback)
chat.addEventListener('play', (e) => {
  if (e.target.tagName !== 'AUDIO') return;
  chat.querySelectorAll('audio').forEach(a => { if (a !== e.target) a.pause(); });
}, true);

function card(s){
  const art = s.artwork_url ? `<img class="art" src="${esc(s.artwork_url)}" alt="">`
                            : `<div class="art"></div>`;
  const audio = s.preview_url
    ? `<audio controls preload="none" src="${esc(s.preview_url)}"></audio>` : '';
  const apple = s.apple_url
    ? `<a class="apple" href="${esc(s.apple_url)}" target="_blank" rel="noopener">Open in Apple Music ↗</a>` : '';
  return `<div class="card">${art}<div class="body">
    <div class="title">${esc(s.title)}</div>
    <div class="artist">${esc(s.artist)}</div>
    <div class="reason">${esc(s.reason)}</div>
    ${audio}${apple}</div></div>`;
}

const LOADER_MESSAGES = [
  'I got your back, just give me a moment…',
  'I can empathize with you, trust me…',
  'You trust me, right?…',
  'Your wait is over, coming right up…'
];

form.addEventListener('submit', async e => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  add(esc(text), 'user');
  input.value = '';
  send.disabled = true;

  let i = 0;
  const loader = add(LOADER_MESSAGES[0], 'loader');
  const spin = setInterval(() => {
    i = (i + 1) % LOADER_MESSAGES.length;
    loader.textContent = LOADER_MESSAGES[i];
  }, 2500);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    clearInterval(spin);
    loader.remove();
    if (data.songs && data.songs.length) {
      if (data.intro) add(esc(data.intro), 'intro');
      const grid = document.createElement('div');
      grid.className = 'songs-grid';
      grid.innerHTML = data.songs.map(card).join('');
      chat.appendChild(grid);
      chat.scrollTop = chat.scrollHeight;
    } else {
      add(esc(data.text || data.intro || "I'm sorry, the token limit for today has been reached. Come tomorrow?"), 'intro');
    }
  } catch (err) {
    clearInterval(spin);
    loader.remove();
    add('Could not reach the agent — is the server running?', 'intro');
  } finally {
    send.disabled = false;
    input.focus();
  }
});