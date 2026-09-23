/**
 * Leaders Series — form handler (Cloudflare Worker)
 *
 * Why this exists: posting straight to MailerLite's embedded-form endpoint
 * always creates subscribers with status "unconfirmed", and unconfirmed
 * subscribers are excluded from groups, so group-join automations never fire.
 * MailerLite's real API can create them as "active" — but it needs a token,
 * and a token in a static page is readable by anyone who views source.
 *
 * So the token lives here instead, as a Worker secret, and the site posts to
 * this Worker rather than to MailerLite directly.
 *
 *   site form  ->  this Worker (holds the token)  ->  MailerLite API
 *
 * Setup:
 *   1. Set the secret:  MAILERLITE_TOKEN
 *   2. Fill in GROUPS.student below with the Student applications group id
 *   3. Deploy, then point the site's forms at the Worker URL
 */

const GROUPS = {
  newsletter: '198740970358965801', // Leaders Series subscribers
  speaker:    '198887399334348742', // Speakers interest
  student:    '198887355633895234', // Student applications
};

// Only these origins may call the Worker. Anything else is refused, so the
// endpoint cannot be used from someone else's page to stuff your list.
const ALLOWED_ORIGINS = [
  'https://leadersseries.com',
  'https://www.leadersseries.com',
  'https://leadersseries.github.io',
];

// Field names accepted per form. Anything not listed is ignored rather than
// forwarded, so a crafted request cannot write arbitrary subscriber fields.
const ALLOWED_FIELDS = {
  newsletter: [],
  speaker:    ['name', 'last_name', 'company', 'job_title', 'area_of_focus'],
  student:    ['name', 'school_or_program', 'where_you_would_contribute', 'cv_link'],
};

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== 'POST') {
      return json({ error: 'Method not allowed' }, 405, origin);
    }
    if (origin && !ALLOWED_ORIGINS.includes(origin)) {
      return json({ error: 'Origin not allowed' }, 403, origin);
    }
    if (!env.MAILERLITE_TOKEN) {
      // Fail loudly in the log, vaguely to the caller.
      console.error('MAILERLITE_TOKEN is not set');
      return json({ error: 'Server not configured' }, 500, origin);
    }

    // Accept either a normal form post or JSON.
    let data;
    try {
      const type = request.headers.get('Content-Type') || '';
      if (type.includes('application/json')) {
        data = await request.json();
      } else {
        data = Object.fromEntries(await request.formData());
      }
    } catch {
      return json({ error: 'Could not read submission' }, 400, origin);
    }

    // Honeypot: real people leave it empty. Answer as if it worked so bots
    // learn nothing, but send nothing on.
    if (data._honey) return json({ ok: true }, 200, origin);

    const form = String(data.form || '').trim();
    if (!GROUPS[form] || GROUPS[form].startsWith('PUT_')) {
      return json({ error: 'Unknown form' }, 400, origin);
    }

    const email = String(data.email || '').trim().toLowerCase();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) {
      return json({ error: 'Please enter a valid email address' }, 400, origin);
    }

    const fields = {};
    for (const key of ALLOWED_FIELDS[form]) {
      const value = data[key];
      if (value !== undefined && String(value).trim() !== '') {
        fields[key] = String(value).trim().slice(0, 1000);
      }
    }

    // status: 'active' is the whole point — it skips confirmation, so the
    // group-join automation fires straight away.
    const payload = {
      email,
      status: 'active',
      groups: [GROUPS[form]],
      ...(Object.keys(fields).length ? { fields } : {}),
    };

    let res, body;
    try {
      res = await fetch('https://connect.mailerlite.com/api/subscribers', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.MAILERLITE_TOKEN}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      body = await res.json().catch(() => ({}));
    } catch (err) {
      console.error('MailerLite request failed', err);
      return json({ error: 'Could not reach the mailing service' }, 502, origin);
    }

    if (!res.ok) {
      // Log the detail, don't leak it to the page.
      console.error('MailerLite rejected the subscriber', res.status, JSON.stringify(body));
      return json({ error: 'Could not complete that just now' }, 502, origin);
    }

    return json({ ok: true, status: body?.data?.status ?? 'active' }, 200, origin);
  },
};
