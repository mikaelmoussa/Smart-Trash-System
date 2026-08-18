const el = (id) => document.getElementById(id);

function setMessage(messageEl, msg, isError = false) {
  if (!messageEl) return;
  messageEl.textContent = msg || '';
  messageEl.style.color = isError ? '#f44336' : '#4CAF50';
}

async function api(path, options) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = data.error || res.statusText || 'Request failed';
    throw new Error(err);
  }
  return data;
}

async function refreshSession() {
  const data = await api('/user/session', { method: 'GET' });
  const loggedIn = !!data.loggedIn;

  el('authView').style.display = loggedIn ? 'none' : 'block';
  el('userView').style.display = loggedIn ? 'block' : 'none';

  if (loggedIn) {
    el('logoutLink').style.display = 'inline-block';
    await loadProfile();
  } else {
    el('logoutLink').style.display = 'none';
  }

  return loggedIn;
}

function renderEntries(entries) {
  const body = el('entriesBody');
  if (!body) return;
  if (!entries || entries.length === 0) {
    body.innerHTML = `<tr><td colspan="4" style="padding:12px; color:#666;">No entries yet.</td></tr>`;
    return;
  }

  body.innerHTML = entries
    .map((e) => {
      return `
        <tr>
          <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${e.date}</td>
          <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${e.items ?? e.amountKg}</td>

          <td style="padding:10px; border-bottom:1px solid #f0f0f0; font-weight:700; color:#1B5E20;">${e.points}</td>
          <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${e.notes ? escapeHtml(e.notes) : '-'}</td>
        </tr>
      `;
    })
    .join('');
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '<')

    .replaceAll('>', '>')

    .replaceAll('"', '"')

    .replaceAll("'", '&#039;');
}


async function loadProfile() {
  const profile = await api('/user/profile', { method: 'GET' });

  el('userNameText').textContent = profile.username || '';
  el('pointsText').textContent = String(profile.totalPoints ?? 0);

  if (profile.lastEntry) {
    el('lastPointsText').textContent = `+${profile.lastEntry.points}`;
    el('lastDateText').textContent = `(${profile.lastEntry.date})`;
  } else {
    el('lastPointsText').textContent = '-';
    el('lastDateText').textContent = '';
  }

  renderEntries(profile.recentEntries || []);
}

async function handleLogin() {
  const msg = el('authMsg');
  setMessage(msg, '');

  const username = el('loginUsername').value.trim();
  const password = el('loginPassword').value;

  try {
    await api('/user/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    await refreshSession();
  } catch (e) {
    setMessage(msg, String(e.message || e), true);
  }
}

async function handleRegister() {
  const msg = el('authMsg');
  setMessage(msg, '');

  const username = el('regUsername').value.trim();
  const password = el('regPassword').value;

  try {
    await api('/user/register', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    // After registration, log in immediately
    await api('/user/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    await refreshSession();
    setMessage(msg, 'Account created!');
  } catch (e) {
    setMessage(msg, String(e.message || e), true);
  }
}

async function handleRecycle() {
  const msg = el('recycleMsg');
  setMessage(msg, '', false);

  const material = (el('materialSelect')?.value || '').toLowerCase();
  const quantityRaw = el('quantityInput')?.value;
  const quantity = Number(quantityRaw);
  const notes = (el('notes')?.value || '').trim();

  if (!material) {
    setMessage(msg, 'Please select a material.', true);
    return;
  }

  if (!Number.isFinite(quantity) || quantity <= 0) {
    setMessage(msg, 'Please enter a valid positive quantity.', true);
    return;
  }

  try {
    const res = await api('/user/recycle', {
      method: 'POST',
      body: JSON.stringify({ material, quantity, notes })
    });

    // Clear quantity (optional UX)
    if (el('quantityInput')) el('quantityInput').value = '';

    setMessage(msg, `Logged! +${res.pointsAwarded} points.`, false);
    await loadProfile();
  } catch (e) {
    setMessage(msg, String(e.message || e), true);
  }
}

async function handleLogout() {
  try {
    await api('/user/logout', { method: 'POST', body: '{}' });
  } catch (_) {}
  await refreshSession();
}

document.addEventListener('DOMContentLoaded', async () => {
  el('logoutLink').addEventListener('click', async (e) => {
    e.preventDefault();
    await handleLogout();
  });

  el('loginBtn').addEventListener('click', handleLogin);
  el('registerBtn').addEventListener('click', handleRegister);
  el('showRegisterBtn').addEventListener('click', () => {
    const card = el('registerCard');
    if (!card) return;
    const isHidden = card.style.display === 'none';
    card.style.display = isHidden ? 'block' : 'none';
  });

  el('recycleBtn').addEventListener('click', handleRecycle);

  // default
  el('logoutLink').style.display = 'none';

  try {
    await refreshSession();
  } catch (_) {
    // if session check fails, keep auth view
    el('authView').style.display = 'block';
    el('userView').style.display = 'none';
  }
});

