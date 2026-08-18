const statusColors = {
  normal: '#4CAF50',
  full: '#f44336',
  maintenance: '#FF9800'
};

const statusIcons = {
  normal: 'check-circle',
  full: 'exclamation-triangle',
  maintenance: 'tools'
};

let map;
let markersById = new Map();
let currentBins = [];

function statusToLabel(status) {
  if (status === 'normal') return 'Normal';
  if (status === 'full') return 'Full';
  if (status === 'maintenance') return 'Maintenance';
  return status;
}

function computeFullnessPercentage(counts) {
  const total = counts.normal + counts.full + counts.maintenance;
  if (total === 0) return 0;
  return Math.round((counts.full / total) * 100);
}

let selectedBinId = null;
let clickLatLng = null;

function el(id) {
  return document.getElementById(id);
}

function setMessage(messageEl, msg, isError = false) {
  if (!messageEl) return;
  messageEl.textContent = msg || '';
  messageEl.style.color = isError ? '#f44336' : '#4CAF50';
}

async function api(path, options) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json'
    },
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
  el('authState').textContent = loggedIn ? 'Logged in' : 'Not logged in';
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
    await ensureAdminMap();
    await loadAndRenderBins();
  } catch (e) {
    setMessage(loginMsg, String(e.message || e), true);
  }
}

async function handleLogout() {
  try {
    await api('/admin/logout', { method: 'POST', body: '{}' });
  } catch (_) {
    // ignore
  }
  await refreshAuth();
}

function markerPopupContent(bin, color) {
  const icon = statusIcons[bin.status] || 'info-circle';
  return `
    <div>
      <h3 style="margin:0 0 6px 0;">${bin.name}</h3>
      <p style="margin:0 0 10px 0;">Status: <strong style="color:${color}">${bin.status.toUpperCase()}</strong></p>
      <div style="display:flex; align-items:center; gap:10px;">
        <i class="fas fa-${icon}" style="color:${color}; font-size:22px;"></i>
        <div style="font-size:12px; color:#666;">Click marker to edit/delete</div>
      </div>
    </div>
  `;
}


function clearMarkers() {
  for (const marker of markersById.values()) {
    try {
      marker.remove();
    } catch (_) {}
  }
  markersById = new Map();
}

function computeCounts(bins) {
  const counts = { normal: 0, full: 0, maintenance: 0 };
  for (const b of bins) {
    if (counts[b.status] !== undefined) counts[b.status]++;
  }
  return counts;
}

function updateStats(counts) {
  el('countNormal').textContent = String(counts.normal);
  el('countFull').textContent = String(counts.full);
  el('countMaintenance').textContent = String(counts.maintenance);
}

function openModalForAdd(latlng) {
  selectedBinId = null;
  clickLatLng = latlng;
  el('binModal').style.display = 'block';
  el('binModal').classList.add('open');



  el('modalTitle').textContent = 'Add Bin';
  el('deleteBtn').style.display = 'none';

  el('binId').value = '';
  el('binName').value = '';
  el('binLat').value = latlng.lat;
  el('binLng').value = latlng.lng;
  el('binStatus').value = 'normal';
  el('modalMsg').textContent = '';
}

function openModalForEdit(bin) {
  selectedBinId = bin.id;
  clickLatLng = null;
  el('binModal').style.display = 'block';
  el('modalTitle').textContent = 'Edit Bin';
  el('deleteBtn').style.display = 'inline-block';

  el('binId').value = bin.id;
  el('binName').value = bin.name;
  el('binLat').value = bin.lat;
  el('binLng').value = bin.lng;
  el('binStatus').value = bin.status;
  el('modalMsg').textContent = '';
}

function closeModal() {
  el('binModal').style.display = 'none';
  selectedBinId = null;
  clickLatLng = null;
}

function renderBinList() {
  const listEl = el('binList');
  if (!listEl) return;

  const counts = computeCounts(currentBins);
  const fullness = computeFullnessPercentage(counts);

  const sorted = [...currentBins].sort((a, b) => {
    const order = { full: 0, maintenance: 1, normal: 2 };
    const oa = order[a.status] ?? 9;
    const ob = order[b.status] ?? 9;
    if (oa !== ob) return oa - ob;
    return a.name.localeCompare(b.name);
  });

  listEl.innerHTML = `
    <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:12px;">
      <div style="flex:1; min-width:260px;">
        <div class="muted" style="margin-bottom:4px;">Overall fullness (Full bins):</div>
        <div style="font-size:18px; font-weight:700; color:#f44336;">${fullness}%</div>
      </div>
      <div style="font-size:12px; color:#666;">
        Normal: ${counts.normal} • Full: ${counts.full} • Maintenance: ${counts.maintenance}
      </div>
    </div>
    <div style="overflow:auto; border:1px solid #eee; border-radius:10px;">
      <table style="width:100%; border-collapse:collapse;">
        <thead>
          <tr style="background:#f8f9fa;">
            <th style="text-align:left; padding:10px; border-bottom:1px solid #eee;">Bin</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #eee;">Status</th>
            <th style="text-align:left; padding:10px; border-bottom:1px solid #eee;">Edit</th>
          </tr>
        </thead>
        <tbody>
          ${sorted.map((bin) => {
            const color = statusColors[bin.status] || '#2196F3';
            return `
              <tr>
                <td style="padding:10px; border-bottom:1px solid #f0f0f0;">${bin.name}</td>
                <td style="padding:10px; border-bottom:1px solid #f0f0f0;">
                  <span style="font-weight:700; color:${color};">${statusToLabel(bin.status)}</span>
                </td>
                <td style="padding:10px; border-bottom:1px solid #f0f0f0;">
                  <button type="button" class="btn" data-bin-id="${bin.id}" style="padding:8px 12px;">Edit</button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;

  listEl.querySelectorAll('button[data-bin-id]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-bin-id');
      const bin = currentBins.find((b) => b.id === id);
      if (bin) openModalForEdit(bin);
    });
  });
}

async function loadAndRenderBins() {
  const data = await api('/api/bins');
  currentBins = data;

  updateStats(computeCounts(currentBins));
  renderBinList();

  clearMarkers();

  if (!map) return;

  currentBins.forEach((bin) => {
    const color = statusColors[bin.status] || '#2196F3';

    const marker = L.circleMarker([bin.lat, bin.lng], {
      radius: 12,
      fillColor: color,
      color: '#000',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95
    }).addTo(map);

    marker.bindPopup(markerPopupContent(bin, color));

    marker.on('click', () => {
      openModalForEdit(bin);
    });

    markersById.set(bin.id, marker);
  });
}

async function ensureAdminMap() {
  if (map) return;

  map = L.map('adminMap', { zoomControl: true }).setView([33.8547, 35.8623], 8);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);

  map.on('click', (e) => {
    openModalForAdd(e.latlng);
  });
}

async function handleSaveBin() {
  const msg = el('modalMsg');
  msg.style.color = '#4CAF50';
  msg.textContent = '';

  const name = el('binName').value.trim();
  const lat = Number(el('binLat').value);
  const lng = Number(el('binLng').value);
  const status = el('binStatus').value;

  const payload = { name, lat, lng, status };

  try {
    if (!selectedBinId) {
      await api('/api/bins', { method: 'POST', body: JSON.stringify(payload) });
      closeModal();
    } else {
      await api(`/api/bins/${selectedBinId}`, { method: 'PUT', body: JSON.stringify(payload) });
      closeModal();
    }
    await loadAndRenderBins();
  } catch (e) {
    msg.style.color = '#f44336';
    msg.textContent = String(e.message || e);
  }
}

async function handleDeleteBin() {
  if (!selectedBinId) return;
  const msg = el('modalMsg');

  const ok = confirm('Delete this bin?');
  if (!ok) return;

  try {
    await api(`/api/bins/${selectedBinId}`, { method: 'DELETE', body: '{}' });
    closeModal();
    await loadAndRenderBins();
  } catch (e) {
    msg.style.color = '#f44336';
    msg.textContent = String(e.message || e);
  }
}

function startLiveRefresh() {
  // Polling every 4 seconds for simplicity.
  setInterval(async () => {
    // Only poll when admin view is visible.
    if (el('adminView').style.display !== 'block') return;
    try {
      await loadAndRenderBins();
    } catch (_) {
      // ignore network/auth errors; UI polling will recover on next refresh.
    }
  }, 4000);
}

document.addEventListener('DOMContentLoaded', async () => {
  // modal wiring
  el('modalClose').addEventListener('click', closeModal);
  el('binForm').addEventListener('submit', (e) => {
    e.preventDefault();
    handleSaveBin();
  });
  el('saveBtn').addEventListener('click', () => handleSaveBin());
  el('deleteBtn').addEventListener('click', () => handleDeleteBin());

  el('refreshBtn').addEventListener('click', () => loadAndRenderBins().catch(() => {}));

  el('loginBtn').addEventListener('click', () => handleLogin());

  el('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    handleLogout();
  });

  // Auth + map init
  try {
    const loggedIn = await refreshAuth();
    if (loggedIn) {
      await ensureAdminMap();
      await loadAndRenderBins();
      startLiveRefresh();
    }
  } catch (_) {
    // ignore
  }
});

