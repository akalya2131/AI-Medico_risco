import { animate } from "https://cdn.jsdelivr.net/npm/motion@11.11.13/+esm";

const openModalButton = document.querySelector('[data-open-add-patient-modal]');
const modal = document.getElementById('add-patient-modal');
const resultModal = document.getElementById('patient-analysis-result-modal');
const createdPatientViewLink = document.getElementById('created-patient-view-link');
const createdPatientRiskScore = document.getElementById('created-patient-risk-score');
const createdPatientRiskLevel = document.getElementById('created-patient-risk-level');
const createdPatientInsights = document.getElementById('created-patient-insights');

function toPayload(form) {
    return {
        patient_name: form.patient_name.value,
        city: form.city?.value || 'Care Hub',
        age: Number(form.age.value),
        gender: form.gender.value,
        bmi: Number(form.bmi.value),
        smoking_status: form.smoking_status.value,
        disease: form.disease.value,
        claim_amount: Number(form.claim_amount.value),
        claim_frequency: Number(form.claim_frequency.value),
    };
}

function updatePreview(container, analysis) {
    const score = container.querySelector('.ai-risk-score');
    const level = container.querySelector('.ai-risk-level');
    const badge = container.querySelector('.ai-risk-badge');
    const insightsList = container.querySelector('.ai-insights-list');
    const recommendationsList = container.querySelector('.ai-recommendations-list');
    const contributionList = container.querySelector('.ai-contribution-list');
    const hintsBox = container.querySelector('.ai-validation-hints');
    const hintsList = container.querySelector('.ai-validation-list');

    if (score) score.textContent = `${analysis.risk_score}`;
    if (level) level.textContent = `${analysis.risk_level} risk profile`;
    if (badge) {
        badge.textContent = analysis.risk_level;
        badge.className = `ai-risk-badge rounded-full px-4 py-2 text-sm font-semibold text-white ${analysis.risk_level === 'High'
            ? 'bg-gradient-to-r from-rose-500 to-red-600'
            : analysis.risk_level === 'Medium'
                ? 'bg-gradient-to-r from-amber-400 to-orange-500'
                : 'bg-gradient-to-r from-emerald-400 to-teal-500'}`;
    }
    if (insightsList) {
        insightsList.innerHTML = analysis.insights.map((item) => `<li>• ${item}</li>`).join('');
    }
    if (recommendationsList) {
        recommendationsList.innerHTML = analysis.recommendations.map((item) => `<li>• ${item}</li>`).join('');
    }
    if (contributionList) {
        contributionList.innerHTML = analysis.contributions.map((item) => `
            <div>
                <div class="mb-1 flex items-center justify-between text-xs text-slate-400">
                    <span>${item.feature}</span>
                    <span>${item.value}</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div class="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500" style="width:${Math.min(100, item.value)}%"></div>
                </div>
            </div>
        `).join('');
    }
    if (hintsBox && hintsList) {
        const hints = analysis.validation_hints || [];
        hintsBox.classList.toggle('hidden', hints.length === 0);
        hintsList.innerHTML = hints.map((item) => `<li>• ${item}</li>`).join('');
    }
}

async function requestPreview(container, form) {
    const endpoint = form.dataset.previewEndpoint;
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toPayload(form)),
    });
    if (!response.ok) return;
    const analysis = await response.json();
    updatePreview(container, analysis);
}

function wireBmiControls(container, form) {
    const bmiRange = container.querySelector('.ai-bmi-range');
    const bmiValue = container.querySelector('.ai-bmi-value');
    const bmiInput = form.bmi;
    const sync = (value) => {
        bmiInput.value = value;
        if (bmiRange) bmiRange.value = value;
        if (bmiValue) bmiValue.textContent = Number(value).toFixed(1);
    };
    bmiRange?.addEventListener('input', () => sync(bmiRange.value));
    bmiInput.addEventListener('input', () => sync(bmiInput.value));
    sync(bmiInput.value);
}

function wireSmokingToggle(container, form) {
    const toggle = container.querySelector('.ai-smoking-toggle');
    const label = container.querySelector('.ai-smoking-label');
    const hidden = form.smoking_status;

    const render = () => {
        const smoking = hidden.value === 'Yes';
        toggle.className = `ai-smoking-toggle relative h-8 w-16 rounded-full transition ${smoking ? 'bg-rose-500/80' : 'bg-slate-700'}`;
        toggle.innerHTML = `<span class="absolute top-1 h-6 w-6 rounded-full bg-white transition ${smoking ? 'left-9' : 'left-1'}"></span>`;
        if (label) label.textContent = smoking ? 'Smoking risk is enabled.' : 'Non-smoking profile selected.';
    };

    toggle?.addEventListener('click', () => {
        hidden.value = hidden.value === 'Yes' ? 'No' : 'Yes';
        render();
        requestPreview(container, form);
    });
    render();
}

function openModal(target) {
    if (!target) return;
    target.classList.remove('hidden');
    target.classList.add('flex');
    animate(target.firstElementChild || target, { opacity: [0.9, 1], transform: ['translateY(14px)', 'translateY(0px)'] }, { duration: 0.22, easing: 'ease-out' });
}

function closeModal(target) {
    if (!target) return;
    target.classList.add('hidden');
    target.classList.remove('flex');
}

function bindForm(form) {
    const container = form;
    wireBmiControls(container, form);
    wireSmokingToggle(container, form);
    requestPreview(container, form);

    let timeout;
    form.querySelectorAll('input, select').forEach((field) => {
        field.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => requestPreview(container, form), 140);
        });
        field.addEventListener('change', () => requestPreview(container, form));
    });

    form.addEventListener('submit', async (event) => {
        if (form.dataset.submitMode === 'page') return;
        event.preventDefault();

        const response = await fetch(form.dataset.submitEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(toPayload(form)),
        });

        if (!response.ok) {
            alert('Unable to analyze and save patient right now.');
            return;
        }

        const payload = await response.json();
        window.dispatchEvent(new CustomEvent('dashboard:patient-created', { detail: payload }));

        if (createdPatientRiskScore) createdPatientRiskScore.textContent = `${payload.patient.ai_analysis.risk_score}`;
        if (createdPatientRiskLevel) createdPatientRiskLevel.textContent = `${payload.patient.ai_analysis.risk_level} risk profile`;
        if (createdPatientInsights) {
            createdPatientInsights.innerHTML = payload.patient.ai_analysis.insights.map((item) => `<li>• ${item}</li>`).join('');
        }
        if (createdPatientViewLink) {
            createdPatientViewLink.href = `/patients/${payload.patient.id}?new_patient=1#overview`;
        }
        closeModal(modal);
        openModal(resultModal);
        form.reset();
        form.smoking_status.value = 'No';
        wireBmiControls(container, form);
        wireSmokingToggle(container, form);
        requestPreview(container, form);
    });
}

openModalButton?.addEventListener('click', () => openModal(modal));
document.querySelectorAll('[data-close-add-patient-modal]').forEach((button) => {
    button.addEventListener('click', () => closeModal(modal));
});
document.querySelectorAll('[data-close-created-patient-modal]').forEach((button) => {
    button.addEventListener('click', () => closeModal(resultModal));
});

document.querySelectorAll('.ai-patient-form').forEach((form) => {
    bindForm(form);
});
