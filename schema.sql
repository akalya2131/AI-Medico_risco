create table if not exists patients (
    id uuid primary key default gen_random_uuid(),
    member_id text not null,
    full_name text not null,
    age integer not null,
    city text not null,
    lat double precision,
    lng double precision,
    bmi numeric,
    medical_history jsonb default '[]'::jsonb,
    created_at timestamptz default now()
);

create table if not exists claims (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references patients(id) on delete cascade,
    provider text not null,
    amount_inr numeric not null,
    status text not null,
    diagnosis_codes jsonb default '[]'::jsonb,
    claim_date date,
    created_at timestamptz default now()
);

create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid references patients(id) on delete cascade,
    title text not null,
    url text not null,
    content_type text,
    created_at timestamptz default now()
);
