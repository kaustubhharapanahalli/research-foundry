# The frontend's production image: Next's standalone output, run by the
# non-root node user. Base images are pinned by digest.
# https://nextjs.org/docs/app/getting-started/deploying#docker
FROM node:26.10.0-trixie-slim@sha256:ec7758ee051e457b468b32bde57b0879010b325bb9862718e9615225ce4aaae1 AS base
ENV NEXT_TELEMETRY_DISABLED=1
# Node 25 and later ship no Corepack, so pnpm is installed by version.
RUN npm install --global pnpm@12.8.1

FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm exec next build

FROM node:26.10.0-trixie-slim@sha256:ec7758ee051e457b468b32bde57b0879010b325bb9862718e9615225ce4aaae1
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
USER node
EXPOSE 3000
# server.js stops accepting requests and finishes the open ones on SIGTERM.
CMD ["node", "server.js"]
