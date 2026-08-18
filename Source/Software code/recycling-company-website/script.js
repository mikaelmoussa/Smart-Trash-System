// Status colors for markers
const statusColors = {
    normal: '#4CAF50',
    full: '#f44336',
    maintenance: '#FF9800'
};

async function fetchPublicBins() {
    const res = await fetch('/api/bins/public');
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const err = data.error || res.statusText || 'Failed to fetch bins';
        throw new Error(err);
    }
    return data;
}

// Initialize map
let map;
async function initMap() {
    if (typeof L === 'undefined') {
        console.error('[LebRecycle] Leaflet (L) is not loaded (offline assets missing).');
        return;
    }

    map = L.map('map', { zoomControl: true }).setView([33.8547, 35.8623], 8);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    const bins = await fetchPublicBins();
    bins.forEach(bin => {
        const color = statusColors[bin.status] || '#2196F3';
        const marker = L.circleMarker([bin.lat, bin.lng], {
            radius: 12,
            fillColor: color,
            color: '#000',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.95
        }).addTo(map);

        marker.bindPopup(`
            <h3>${bin.name}</h3>
            <p>Status: <strong style="color: ${color}">${bin.status.toUpperCase()}</strong></p>
            <i class="fas fa-${bin.status === 'normal' ? 'check-circle' : bin.status === 'full' ? 'exclamation-triangle' : 'tools'} fa-2x" style="color: ${color}"></i>
        `);
    });
}


// Charts data
const recycledData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
        label: 'Recycled Trash (tons)',
        data: [120, 190, 300, 500, 200, 300],
        backgroundColor: '#4CAF50',
        borderColor: '#388E3C',
        borderWidth: 2
    }]
};

const trashData = {
    labels: ['Plastic', 'Paper', 'Glass', 'Metal'],
    datasets: [{
        label: 'Trash Composition (%)',
        data: [25, 35, 25,15],
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#9966FF']
    }]
};

// Hero waste pie chart data (15% recycled, 85% landfill)
const heroWasteData = {
    labels: ['Recycled', 'Landfill'],
    datasets: [{
        data: [15, 85],
        backgroundColor: ['#4CAF50', '#f44336'],
        borderWidth: 0
    }]
};

function initCharts() {
    const heroCanvas = document.getElementById('heroWasteChart');
    if (heroCanvas) {
        new Chart(heroCanvas, {
            type: 'pie',
            data: heroWasteData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#fff',
                            font: { size: 14 }
                        }
                    }
                }
            }
        });
    }

    new Chart(document.getElementById('recycledChart'), {
        type: 'bar',
        data: recycledData,
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    new Chart(document.getElementById('trashChart'), {
        type: 'doughnut',
        data: trashData,
        options: {
            responsive: true,
            cutout: '60%'
        }
    });
}


// Smooth scrolling for nav links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Side Chat functionality
function toggleSideChat() {
    const panel = document.getElementById('sideChat');
    panel.classList.toggle('open');
}

function closeSideChat() {
    document.getElementById('sideChat').classList.remove('open');
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const mapEl = document.getElementById('map');
        if (!mapEl) return;

        // Ensure Leaflet container is visible and has layout before init.
        // If CSS or layout delays loading, ensure a real size before init.
        mapEl.style.display = 'block';
        mapEl.style.minHeight = '480px';

        initMap();

        // Invalidate size after a couple of layout passes.
        setTimeout(() => {
            if (map && typeof map.invalidateSize === 'function') map.invalidateSize();
        }, 0);

        setTimeout(() => {
            if (map && typeof map.invalidateSize === 'function') map.invalidateSize();
        }, 50);
    }, 0);

    // Re-check after chart init (layout changes can affect Leaflet tiles)
    setTimeout(() => { if (map && typeof map.invalidateSize === 'function') map.invalidateSize(); }, 200);

    initCharts();


// Side chat event listeners - bottom + top nav buttons
    document.querySelectorAll('#chatBtn, #topChatBtn').forEach(btn => {
        btn.addEventListener('click', toggleSideChat);
    });

    document.getElementById('sideChat').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeSideChat();
    });

});


