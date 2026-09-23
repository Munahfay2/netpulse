# NetPulse frontend

React + TypeScript + Tailwind v4 + Recharts NOC dashboard.

See the repo root's `README.md` for setup instructions, `API.md` for the
backend endpoints this talks to, and `ARCHITECTURE.md` for the overall
system design. Quick start:

```bash
npm install
npm run dev
```

Vite proxies `/api/*` to `http://localhost:8000` in dev (see
`vite.config.ts`). For a production build served from a different origin
than the backend, set `VITE_API_URL` — see `.env.example`.
