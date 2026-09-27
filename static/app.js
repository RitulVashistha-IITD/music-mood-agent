const chat = document.getElementById('chat');
const form = document.getElementById('form');
const input = document.getElementById('input');
const send = document.getElementById('send');

const add = (html, cls) => {
  const d = document.createElement('div');
  d.className = cls;
  d.innerHTML = html;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
};
const esc = s => (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// When any preview starts, pause every other one (single-track playback).
chat.addEventListener('play', (e) => {
  if (e.target.tagName !== 'AUDIO') return;
  chat.querySelectorAll('audio').forEach(a => { if (a !== e.target) a.pause(); });
}, true);

function card(s){
  const art = s.artwork_url ? `<img src="${esc(s.artwork_url)}" alt="">` : `<img alt="">`;
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

form.addEventListener('submit', async e => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  add(esc(text), 'user');
  input.value = '';
  send.disabled = true;
  const loader = add('finding the right songs', 'loader');
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    loader.remove();
    if (data.songs && data.songs.length) {
      if (data.intro) add(esc(data.intro), 'intro');
      data.songs.forEach(s => add(card(s), ''));
    } else {
      add(esc(data.text || 'Hmm, nothing came back — try again?'), 'intro');
    }
  } catch (err) {
    loader.remove();
    add('Could not reach the agent — is the server running?', 'intro');
  } finally {
    send.disabled = false;
    input.focus();
  }
});