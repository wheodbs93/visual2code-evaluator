#!/usr/bin/env bash
set -euo pipefail
# Experimental production renderer build helper.
# Expects SOURCE_DIR and IMAGE_NAME. Generates a container image that builds a Node app
# and serves a conventional static output directory when available.
: "${SOURCE_DIR:?SOURCE_DIR is required}"
: "${IMAGE_NAME:?IMAGE_NAME is required}"
cat > "${SOURCE_DIR}/Dockerfile.render" <<'EOF'
FROM node:22-bookworm-slim
WORKDIR /app
COPY . /app
RUN if [ -f package-lock.json ]; then npm ci; elif [ -f pnpm-lock.yaml ]; then corepack enable && pnpm install --frozen-lockfile; elif [ -f yarn.lock ]; then corepack enable && yarn install --frozen-lockfile; elif [ -f package.json ]; then npm install; fi
RUN if [ -f package.json ]; then npm run build --if-present; fi
EXPOSE 3000
CMD ["sh","-lc","if [ -d dist ]; then npx --yes serve -s dist -l 3000; elif [ -d build ]; then npx --yes serve -s build -l 3000; elif [ -f package.json ]; then npm start -- --hostname 0.0.0.0 --port 3000; else python -m http.server 3000 --bind 0.0.0.0; fi"]
EOF
docker build -f "${SOURCE_DIR}/Dockerfile.render" -t "${IMAGE_NAME}" "${SOURCE_DIR}"
