# Next.js 15 Build Issue — RESOLVED (2026-10-08)

## Symptom
`pnpm --filter @aigestion/landing build` failed with a misleading error:
`Error: <Html> should not be imported outside of pages/_document` on
`/_error: /404` — no source file actually imported `<Html>`.

## Root causes (two, stacked)

1. **`NODE_ENV=development` set at Windows User level.** `next build` then
   loads React's development bundle; the production error-page rendering
   path breaks and surfaces as the bogus `<Html>` import error. Local
   machine only — GitHub runners do not define NODE_ENV (CI is green).
2. **`experimental: { serverActions: true }` in `next.config.js`.**
   Next 15 expects an object here; a boolean is invalid and destabilizes
   the build config.

## Fixes applied

- Removed the invalid `experimental.serverActions` block from
  `apps/landing/next.config.js` (Server Actions are stable in Next 15;
  no opt-in required).
- Deleted the experimental `src/app/error/` and `src/app/not-found/`
  scratch dirs under `apps/landing`.
- Local builds must force production mode:
  PowerShell: `$env:NODE_ENV='production'; pnpm --filter @aigestion/landing build`
  (do NOT change the user-level env var without operator approval).

## Status

- Local build: 6/6 static pages (incl. `api/download-apk`, `api/qr-apk`).
- CI `Build (landing)` green: run `37855395116` (2026-10-08).
- Earlier workaround attempts (force-dynamic error pages, `output: 'export'`)
  are obsolete — do not reintroduce them.
