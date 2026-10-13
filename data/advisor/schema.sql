create table if not exists public.advisor_leads (
  id uuid primary key default gen_random_uuid(),
  course_interest text not null default 'MBA',
  channel text not null check (channel in ('email', 'whatsapp')),
  email text,
  whatsapp text,
  requested_service text not null default 'advisor_follow_up',
  page_path text not null default '/',
  conversation_summary text not null default '',
  marketing_consent boolean not null default false,
  consent_notice_version text not null default 'advisor-v1',
  created_at timestamptz not null default now(),
  constraint advisor_leads_contact_required check (
    (channel = 'email' and email is not null and length(email) > 3 and whatsapp is null)
    or
    (channel = 'whatsapp' and whatsapp is not null and length(whatsapp) >= 8 and email is null)
  )
);

alter table public.advisor_leads enable row level security;

-- No browser-facing policies are created. Inserts use the server-side service role
-- key only; never expose SUPABASE_SERVICE_ROLE_KEY to client-side JavaScript.
revoke all on table public.advisor_leads from anon, authenticated;
grant insert on table public.advisor_leads to service_role;