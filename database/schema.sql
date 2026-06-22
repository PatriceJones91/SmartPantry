-- Smart Pantry 2.0 Supabase schema
-- Run this in Supabase SQL Editor before starting the backend.

create extension if not exists "pgcrypto";

create table if not exists sp2_users (
    id uuid primary key default gen_random_uuid(),
    username text unique not null,
    password_hash text not null,
    role text not null default 'participant',
    created_at timestamptz default now()
);

create table if not exists sp2_pantry_items (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references sp2_users(id) on delete cascade,
    item_name text not null,
    category text default 'Other',
    quantity numeric default 1,
    unit text default 'item',
    container_type text default '',
    expiration_date date,
    status text default 'available',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists sp2_surveys (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references sp2_users(id) on delete cascade,
    survey_type text not null,
    responses jsonb not null default '{}'::jsonb,
    comments text default '',
    created_at timestamptz default now()
);

create table if not exists sp2_recommendation_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references sp2_users(id) on delete cascade,
    recipe_name text not null,
    action text not null,
    score numeric,
    feedback text default '',
    used_ingredients jsonb default '[]'::jsonb,
    created_at timestamptz default now()
);

create table if not exists sp2_ingredient_usage_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references sp2_users(id) on delete cascade,
    pantry_item_id uuid references sp2_pantry_items(id) on delete set null,
    item_name text,
    action text,
    amount_used numeric,
    notes text default '',
    created_at timestamptz default now()
);

-- Demo admin account:
-- username: admin
-- password: Admin123!
insert into sp2_users (username, password_hash, role)
values ('admin', '3eb3fe66b31e3b4d10fa70b5cad49c7112294af6ae4e476a1c405155d45aa121', 'admin')
on conflict (username) do nothing;
