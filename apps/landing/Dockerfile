# Workspace-aware build: run with context = repo root, e.g.
#   docker build -f apps/landing/Dockerfile .
FROM node:24-alpine AS base

FROM base AS deps
WORKDIR /app
# Root manifests + workspace member manifests for a reproducible install.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/landing/package.json apps/landing/
COPY apps/daniela-shell/package.json apps/daniela-shell/
COPY apps/mobile-pwa/package.json apps/mobile-pwa/
COPY packages/three-daniela/package.json packages/three-daniela/
COPY packages/ui/package.json packages/ui/
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Re-install to fix pnpm symlinks after COPY
RUN corepack enable pnpm && pnpm install --frozen-lockfile --offline
RUN corepack enable pnpm && pnpm --filter @aigestion/three-daniela build && pnpm --filter @aigestion/ui build && pnpm --filter @aigestion/landing build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/landing/public ./public
COPY --from=builder /app/apps/landing/.next/standalone ./
COPY --from=builder /app/apps/landing/.next/static ./.next/static
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]