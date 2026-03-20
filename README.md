# AI-Powered Patient Risk Prediction & Healthcare Intelligence

A premium, production-style Flask scaffold for a futuristic medical command center with a modular backend, Supabase-ready service layer, explainable patient risk engine, Chart.js analytics, Leaflet hospital intelligence, and a document vault.

## Stack

- **Backend:** Flask with modular blueprints in `app/routes/`
- **Database/Auth/Storage:** Supabase-ready repository layer with demo-mode fallback
- **Frontend:** Tailwind CSS 4, Chart.js, Leaflet, and a premium command-center HTML layout
- **Intelligence:** `risk_engine.py` with explainable 1–5 scoring and preventive care recommendations

## Project structure

```text
app/
  routes/
  services/
  utils/
static/js/
templates/
risk_engine.py
schema.sql
```

## Environment

Copy `.env.example` to `.env` and set:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_BUCKET`
- `FLASK_SECRET_KEY`

If Supabase is not configured, the dashboard runs in **demo mode** using curated patient and hospital data.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app.py run --debug
```

## API endpoints

- `POST /api/predict` — Returns explainable risk JSON for a saved `patient_id` or an ad-hoc payload.
- `GET /api/patients/<patient_id>` — Returns drill-down patient detail JSON for the dashboard morph view.
- `POST /api/simulator` — Powers the live BMI and age what-if simulator.
