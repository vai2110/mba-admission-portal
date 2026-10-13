function hasAllowedOrigin(req) {
  const origin = req.headers.origin;
  if (!origin) return true; // Non-browser callers may omit Origin; protect browser cross-origin requests.
  try {
    const parsed = new URL(origin);
    const requestHost = String(req.headers.host || "").toLowerCase();
    if (parsed.protocol !== "https:" && parsed.hostname !== "localhost") return false;
    if (parsed.host.toLowerCase() === requestHost) return true;
    if (["collegedecoded.in", "www.collegedecoded.in"].includes(parsed.hostname.toLowerCase())) return true;
    return parsed.hostname.endsWith(".vercel.app") && parsed.host.toLowerCase() === requestHost;
  } catch (_) {
    return false;
  }
}

function send(res, status, payload) {
  res.status(status).setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  return res.end(JSON.stringify(payload));
}

function clean(value, max = 500) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}

module.exports = async function handler(req, res) {
  if (!hasAllowedOrigin(req)) return send(res, 403, { error: "Request origin not allowed." });
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return send(res, 405, { error: "Method not allowed." });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!supabaseUrl || !serviceKey) {
    return send(res, 503, {
      error: "Saving follow-up requests is not available yet. You can continue using the advisor without sharing contact details."
    });
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch (_) { body = null; }
  }
  if (!body || typeof body !== "object") {
    return send(res, 400, { error: "Please check the details and try again." });
  }

  const channel = clean(body.channel, 20);
  const email = clean(body.email, 254).toLowerCase();
  const whatsapp = clean(body.whatsapp, 30);
  const service = clean(body.service, 60) || "advisor_follow_up";
  const courseInterest = "MBA";
  const pagePath = clean(body.pagePath, 300);
  const summary = clean(body.summary, 1500);
  const marketingConsent = body.marketingConsent === true;

  if (!["email", "whatsapp"].includes(channel)) {
    return send(res, 400, { error: "Choose email or WhatsApp for your request." });
  }
  if (channel === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return send(res, 400, { error: "Enter a valid email address." });
  }
  if (channel === "whatsapp" && !/^\+?[0-9 ()-]{8,20}$/.test(whatsapp)) {
    return send(res, 400, { error: "Enter a valid WhatsApp number, including country code if possible." });
  }

  let safePagePath = pagePath.startsWith("/") && !pagePath.startsWith("//") ? pagePath : "/";
  const row = {
    course_interest: courseInterest,
    channel,
    email: channel === "email" ? email : null,
    whatsapp: channel === "whatsapp" ? whatsapp.replace(/[ ()-]/g, "") : null,
    requested_service: service,
    page_path: safePagePath,
    conversation_summary: summary,
    marketing_consent: marketingConsent,
    consent_notice_version: "advisor-v1",
    created_at: new Date().toISOString()
  };

  let response;
  try {
    const base = supabaseUrl.replace(/\/+$/, "");
    response = await fetch(base + "/rest/v1/advisor_leads", {
      method: "POST",
      headers: {
        "apikey": serviceKey,
        "Authorization": "Bearer " + serviceKey,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
      },
      body: JSON.stringify(row)
    });
  } catch (_) {
    return send(res, 502, { error: "I couldn't save that request right now. Please try again later." });
  }

  if (!response.ok) {
    console.error("CollegeDecoded advisor lead storage error:", response.status);
    return send(res, 502, { error: "I couldn't save that request right now. Please try again later." });
  }

  return send(res, 200, {
    ok: true,
    message: "Your request has been recorded. This does not subscribe you to marketing updates unless you separately opted in."
  });
};