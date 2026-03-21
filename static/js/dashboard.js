import { animate } from "https://cdn.jsdelivr.net/npm/motion@11.11.13/+esm";

const boot = window.dashboardBoot;
const patientDirectory = document.getElementById('patient-directory');
const patientSearch = document.getElementById('patient-search');
const searchStatus = document.getElementById('search-status');
const highRiskGrid = document.getElementById('high-risk-grid');
const highRiskSummary = document.getElementById('high-risk-summary');
const alertBanner = document.getElementById('risk-alert-banner');
const alertBannerCount = document.getElementById('risk-alert-banner-count');
const alertSummaryValue = document.getElementById('risk-alert-summary-value');
let diseaseChart;
let riskChart;
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

function renderStats() {
    const totalPatients = document.getElementById('stat-total-patients');
    const averageRisk = document.getElementById('stat-average-risk');
    const claimValue = document.getElementById('stat-claim-value');
    const highRiskValue = document.getElementById('stat-high-risk');
    if (totalPatients) totalPatients.textContent = `${boot.stats.total_patients}`;
    if (averageRisk) averageRisk.textContent = `${boot.stats.average_risk}/5`;
    if (claimValue) claimValue.textContent = `₹ ${Math.round(boot.stats.total_claims_inr).toLocaleString()}`;
    if (highRiskValue) highRiskValue.textContent = `${boot.stats.high_risk_alerts}`;
    if (highRiskSummary) highRiskSummary.textContent = `⚠️ ${boot.highRiskPatients.length} High Risk Patients`;
    if (alertSummaryValue) alertSummaryValue.textContent = `${boot.stats.high_risk_alerts}`;
    if (alertBannerCount) {
        alertBannerCount.textContent = `${boot.stats.high_risk_alerts} High Risk Patients require immediate review.`;
    }
    if (alertBanner) {
        alertBanner.classList.toggle('hidden', boot.stats.high_risk_alerts === 0);
    }
}

function renderDirectory() {
    if (!patientDirectory) return;
    patientDirectory.innerHTML = boot.patients.map((patient) => `
        <a href="/patients/${patient.id}" class="patient-card patient-card-link block w-full rounded-3xl border p-4 text-left transition hover:border-teal-300/30 hover:bg-white/10 ${patient.is_high_risk ? 'high-risk-glow border-rose-400/35 bg-rose-500/10' : 'border-white/10 bg-white/5'}" data-search-text="${`${patient.full_name} ${patient.city} ${patient.member_id} ${patient.primary_diagnosis} ${patient.risk.risk_label}`.toLowerCase()}">
            <div class="flex items-start justify-between gap-3">
                <div>
                    <p class="font-medium text-white">${patient.is_high_risk ? '⚠️ ' : ''}${patient.full_name}</p>
                    <p class="mt-1 text-xs uppercase tracking-[0.25em] text-slate-500">${patient.city} · ${patient.member_id}</p>
                    <p class="mt-2 text-sm text-slate-400">${patient.primary_diagnosis}</p>
                </div>
                <div class="flex flex-col items-end gap-2">
                    <span class="rounded-full border border-teal-300/20 bg-teal-300/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-teal-100">${patient.risk.risk_label}</span>
                    ${patient.is_high_risk ? '<span class="rounded-full border border-rose-300/25 bg-rose-300/15 px-3 py-1 text-xs uppercase tracking-[0.2em] text-rose-100">High Risk</span>' : ''}
                </div>
            </div>
        </a>
    `).join('');
    runSearch();
}

function renderHighRiskQueue() {
    if (!highRiskGrid) return;
    if (!boot.highRiskPatients.length) {
        highRiskGrid.innerHTML = '<div class="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400 lg:col-span-3">No patients are currently in the high-risk queue.</div>';
        return;
    }
    highRiskGrid.innerHTML = boot.highRiskPatients.map((patient) => `
        <a href="/patients/${patient.id}" class="high-risk-glow block rounded-3xl border bg-rose-500/10 p-5 transition hover:bg-rose-500/15">
            <div class="flex items-start justify-between gap-4">
                <div>
                    <p class="font-medium text-white">⚠️ ${patient.full_name}</p>
                    <p class="mt-1 text-sm text-rose-100/80">${patient.primary_diagnosis} · ${patient.city}</p>
                    <p class="mt-3 text-xs uppercase tracking-[0.25em] text-rose-100/60">Closest hospital</p>
                    <p class="mt-1 text-sm text-slate-300">${patient.closest_hospital?.name || 'Monitoring only'}</p>
                </div>
                <span class="rounded-full border border-rose-300/25 bg-rose-300/15 px-3 py-1 text-xs uppercase tracking-[0.2em] text-rose-100">High Risk</span>
            </div>
        </a>
    `).join('');
}

function renderAnalyticsCharts() {
    const diseaseCanvas = document.getElementById('diseaseFrequencyChart');
    const riskCanvas = document.getElementById('riskDistributionChart');
    if (!diseaseCanvas || !riskCanvas || !boot.analytics) return;

    const diseaseEntries = Object.entries(boot.analytics.disease_counts || {}).slice(0, 8);
    const diseaseLabels = diseaseEntries.map(([label]) => label.toUpperCase());
    const diseaseValues = diseaseEntries.map(([, value]) => value);
    const riskLabels = Object.keys(boot.analytics.risk_distribution || {});
    const riskValues = Object.values(boot.analytics.risk_distribution || {});

    if (diseaseChart) diseaseChart.destroy();
    diseaseChart = new Chart(diseaseCanvas, {
        type: 'bar',
        data: {
            labels: diseaseLabels,
            datasets: [{
                label: 'Disease frequency',
                data: diseaseValues,
                backgroundColor: ['#34d399', '#22d3ee', '#818cf8', '#a78bfa', '#f472b6', '#fb7185', '#f59e0b', '#facc15'],
                borderRadius: 10,
            }],
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(148, 163, 184, 0.08)' } },
                y: { beginAtZero: true, ticks: { color: '#cbd5e1', precision: 0 }, grid: { color: 'rgba(148, 163, 184, 0.08)' } },
            },
        },
    });

    if (riskChart) riskChart.destroy();
    riskChart = new Chart(riskCanvas, {
        type: 'doughnut',
        data: {
            labels: riskLabels.map((label) => `Risk ${label}`),
            datasets: [{
                data: riskValues,
                backgroundColor: ['#22c55e', '#38bdf8', '#a78bfa', '#fb7185', '#ef4444'],
                borderWidth: 0,
            }],
        },
        options: {
            cutout: '65%',
            plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } },
        },
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
window.addEventListener('dashboard:patient-created', (event) => {
    const payload = event.detail;
    boot.patients = payload.dashboard.patients;
    boot.highRiskPatients = payload.dashboard.high_risk_patients;
    boot.analytics = payload.dashboard.analytics;
    boot.stats = payload.dashboard.stats;
    renderDirectory();
    renderHighRiskQueue();
    renderStats();
    renderAnalyticsCharts();
    renderMap();
});
renderDirectory();
renderHighRiskQueue();
renderStats();
renderAnalyticsCharts();
renderMap();
