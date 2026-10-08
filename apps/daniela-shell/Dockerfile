# Workspace-aware build: run with context = repo root, e.g.
#   docker build -f apps/daniela-shell/Dockerfile .
FROM node:24-alpine AS base

# Build arg to invalidate cache when lockfile changes
ARG LOCKFILE_HASH

FROM base AS deps
WORKDIR /app
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
# Re-install to fix pnpm symlinks after COPY (no --offline to pick up lockfile changes)
RUN corepack enable pnpm && pnpm install --frozen-lockfile
RUN corepack enable pnpm && pnpm --filter @aigestion/three-daniela build && pnpm --filter @aigestion/ui build && pnpm --filter @aigestion/daniela-shell build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/daniela-shell/public ./public
COPY --from=builder /app/apps/daniela-shell/.next/standalone ./
COPY --from=builder /app/apps/daniela-shell/.next/static ./.next/static
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]