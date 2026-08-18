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

async function refreshAuth() {
  const auth = await api('/admin/session', { method: 'GET', headers: {} });
  const loggedIn = !!auth.loggedIn;
  el('loginView').style.display = loggedIn ? 'none' : 'block';
  el('adminView').style.display = loggedIn ? 'block' : 'none';
  if (el('authState')) el('authState').textContent = loggedIn ? 'Logged in' : 'Not logged in';
  return loggedIn;
}

async function handleLogin() {
  const loginMsg = el('loginMsg');
  setMessage(loginMsg, '', false);

  const username = el('username').value;
  const password = el('password').value;

  try {
    await api('/admin/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    await refreshAuth();
    await loadUsers();
  } catch (e) {
    setMessage(loginMsg, String(e.message || e), true);
  }
}

async function handleLogout() {
  try {
    await api('/admin/logout', { method: 'POST', body: '{}' });
  } catch (_) {}
  await refreshAuth();
}

function renderUsers(users) {
  const body = el('userListBody');
  if (!body) return;

  if (!users || users.length === 0) {
    body.innerHTML = `<tr><td colspan="4" style="padding:12px; color:#666;">No users found.</td></tr>`;
    return;
  }

  body.innerHTML = users.map(u => {
    return `
      <tr>
        <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${u.username}</td>
        <td style="padding:10px; border-bottom:1px solid #f0f0f0; font-weight:700; color:#1B5E20;">${u.totalPoints ?? 0}</td>
        <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${u.recentEntries ?? 0}</td>
        <td style="padding:10px; border-bottom:1px solid #f0f0f0;">
          <button class="btn btn-danger" type="button" data-user-id="${u.id}" style="padding:8px 12px;">Delete</button>
        </td>
      </tr>
    `;
  }).join('');

  body.querySelectorAll('button[data-user-id]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-user-id');
      const user = users.find(x => x.id === id);
      if (!user) return;

      const ok = confirm(`Delete account for ${user.username}?\n\nPress OK to DELETE ONLY account. Press Cancel?`);
      if (!ok) return;

      // Simple flow: user picks delete history or keep it
      const deleteHistory = confirm('Also delete recycling history for this user?');

      try {
        await api(`/api/users/${id}`, {
          method: 'DELETE',
          body: JSON.stringify({ deleteHistory })
        });
        await loadUsers();
      } catch (e) {
        alert(String(e.message || e));
      }
    });
  });
}

async function loadUsers() {
  const users = await api('/api/users', { method: 'GET' });
  renderUsers(users);
}

document.addEventListener('DOMContentLoaded', async () => {
  el('loginBtn').addEventListener('click', handleLogin);
  el('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    handleLogout();
  });
  el('refreshBtn').addEventListener('click', () => loadUsers().catch(() => {}));

  try {
    const loggedIn = await refreshAuth();
    if (loggedIn) await loadUsers();
  } catch (_) {}
});

