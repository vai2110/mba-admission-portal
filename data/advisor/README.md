# CollegeDecoded AI Advisor

This folder contains setup guidance and the SQL schema for the initial MBA-advisor pilot.

## Required Vercel environment variables

- \`OPENAI_API_KEY\`: server-side OpenAI API key with Responses API access.
- \`OPENAI_MODEL\`: optional model override; default is \`gpt-4.1-mini\`.
- \`SUPABASE_URL\`: Supabase project URL, required to store follow-up requests.
- \`SUPABASE_SERVICE_ROLE_KEY\`: server-only Supabase service role key. Never expose it to browser code.

Add these variables in Vercel Project Settings → Environment Variables for Preview first. Redeploy the preview after adding them. Do not commit keys to GitHub.

The chat endpoint uses the Responses API web-search tool for current information. Check model/tool availability and account permissions in the target OpenAI project before launch.

## Lead storage

Run \`schema.sql\` in the Supabase SQL editor. The API only stores a request after the user explicitly submits the contact form. Email/WhatsApp delivery is not wired in this first implementation; the endpoint records a consent-aware follow-up request. Do not tell users a message has been sent.

## Current MVP boundaries

- MBA/PGDM-focused counselling.
- Uses current page content as context and web search for current claims.
- Does not guarantee admission or calculate validated admission probabilities.
- Does not yet send emails or WhatsApp messages.
- Do not launch contact capture until the database schema and privacy notice have been reviewed.
- Configure platform-level rate limits / abuse protection before public rollout.
