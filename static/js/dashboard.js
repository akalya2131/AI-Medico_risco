import { animate } from "https://cdn.jsdelivr.net/npm/motion@11.11.13/+esm";

const boot = window.dashboardBoot;
const patientDirectory = document.getElementById('patient-directory');
const patientSearch = document.getElementById('patient-search');
const searchStatus = document.getElementById('search-status');
let map;
let mapMarkers = [];

function runSearch() {
    const query = (patientSearch?.value || '').trim().toLowerCase();
    const cards = [...document.querySelectorAll('.patient-card')];
    let visibleCount = 0;

    cards.forEach((card) => {
        const matches = card.dataset.searchText.includes(query);
        card.classList.toggle('hidden', !matches);
        if (matches) visibleCount += 1;
    });

    searchStatus.textContent = query
        ? `${visibleCount} patient${visibleCount === 1 ? '' : 's'} match “${patientSearch.value}”.`
        : 'Type to filter the directory in real time.';
}

function renderMap() {
    if (!map) {
        map = L.map('india-map').setView([22.9734, 78.6569], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    }

    mapMarkers.forEach((marker) => marker.remove());
    mapMarkers = [];

    boot.hospitals.forEach((hospital) => {
        const marker = L.marker([hospital.lat, hospital.lng]).addTo(map).bindPopup(`<strong>${hospital.name}</strong><br>${hospital.specialty}`);
        mapMarkers.push(marker);
    });

    boot.patients.filter((patient) => patient.risk.risk_score >= 4).forEach((patient) => {
        const marker = L.circleMarker([patient.lat, patient.lng], { radius: 10, color: '#5eead4', fillOpacity: 0.85 }).addTo(map).bindPopup(`<strong>${patient.full_name}</strong><br>${patient.risk.risk_label}`);
        mapMarkers.push(marker);
        if (patient.closest_hospital) {
            const line = L.polyline([[patient.lat, patient.lng], [patient.closest_hospital.lat, patient.closest_hospital.lng]], { color: '#34d399', dashArray: '6 10' }).addTo(map);
            mapMarkers.push(line);
        }
    });
}

patientDirectory?.addEventListener('click', (event) => {
    const card = event.target.closest('.patient-card-link');
    if (!card || card.classList.contains('hidden')) return;
    event.preventDefault();
    animate(card, { scale: [1, 0.985, 1] }, { duration: 0.2, easing: 'ease-out' });
    setTimeout(() => {
        window.location.href = card.href;
    }, 180);
});

patientSearch?.addEventListener('input', runSearch);
renderMap();
