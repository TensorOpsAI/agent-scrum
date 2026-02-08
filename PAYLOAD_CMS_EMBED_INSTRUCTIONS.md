# Instructions: Embed Payload CMS into Agent Scrum

## Context

Agent Scrum is a React + FastAPI app deployed on Cloud Run at:
```
https://agent-scrum-526473703868.us-central1.run.app
```

We want to embed a Payload CMS instance (also hosted on Cloud Run, different GCP project) into the Agent Scrum frontend. The CMS will be used to manage content that gets displayed within the Agent Scrum app.

## What You Need To Do

### 1. Allow iframe embedding from the Agent Scrum domain

By default, Payload CMS sets `X-Frame-Options: DENY` which blocks iframe embedding. You need to allow it for the Agent Scrum origin.

**In your Payload config (e.g. `payload.config.ts` or `server.ts`):**

Add/modify the Content-Security-Policy and X-Frame-Options headers to allow embedding from the Agent Scrum domain:

```typescript
// If using Express/Next.js custom server, add this middleware:
app.use((req, res, next) => {
  // Allow embedding from Agent Scrum
  res.setHeader('X-Frame-Options', 'ALLOW-FROM https://agent-scrum-526473703868.us-central1.run.app');
  res.setHeader(
    'Content-Security-Policy',
    "frame-ancestors 'self' https://agent-scrum-526473703868.us-central1.run.app"
  );
  next();
});
```

> Note: `X-Frame-Options: ALLOW-FROM` is deprecated in modern browsers. The `Content-Security-Policy: frame-ancestors` directive is what actually works. Keep both for compatibility.

### 2. Enable CORS for the Agent Scrum origin

If the Agent Scrum frontend will also make direct API calls to Payload (not just iframe), add CORS:

```typescript
import cors from 'cors';

app.use(cors({
  origin: [
    'https://agent-scrum-526473703868.us-central1.run.app',
    'http://localhost:5173', // local dev
  ],
  credentials: true,
}));
```

### 3. Set `SameSite=None; Secure` on auth cookies

For Payload's authentication to work inside an iframe (cross-origin), cookies must be sent cross-site:

```typescript
// In your Payload config:
export default buildConfig({
  // ... other config
  cookiePrefix: 'payload',
  csrf: [
    'https://agent-scrum-526473703868.us-central1.run.app',
  ],
  // If using custom cookie settings:
  cookies: {
    secure: true,
    sameSite: 'none',
  },
});
```

### 4. Deploy with these changes

After making the changes above, redeploy your Payload CMS Cloud Run service. Then provide the Cloud Run URL (e.g. `https://your-payload-cms-XXXXX.us-central1.run.app`) so it can be embedded in the Agent Scrum frontend.

## How It Will Be Embedded (Agent Scrum Side)

On the Agent Scrum side, the Payload CMS will be embedded as an iframe in a dedicated panel/page. The Agent Scrum frontend will:

1. Load the Payload CMS admin UI in an iframe pointed at `<YOUR_PAYLOAD_CLOUD_RUN_URL>/admin`
2. Optionally use Payload's REST/GraphQL API directly for fetching content to display in the app

The Agent Scrum app will use the Payload CMS URL via an environment variable:
```
VITE_PAYLOAD_CMS_URL=https://your-payload-cms-XXXXX.us-central1.run.app
```

## Summary of Changes Needed

| File | Change |
|------|--------|
| Server config / middleware | Add `frame-ancestors` CSP header allowing Agent Scrum origin |
| Server config / middleware | Add CORS for Agent Scrum origin |
| Payload config | Set `SameSite=None; Secure` on cookies, add Agent Scrum to CSRF allowlist |
| Cloud Run | Redeploy after changes |
