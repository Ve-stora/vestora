# Vestora frontend — dev image
# Note: docker-compose.yml overrides CMD with `npm run dev -- --host`,
# so the CMD here is just a sane default for `docker build` standalone use.

FROM node:20-alpine

WORKDIR /app

# Install deps first so this layer is cached unless package*.json changes.
# (The compose file also bind-mounts ./frontend:/app and keeps
# /app/node_modules as an anonymous volume, so this install only matters
# for the very first `docker compose up --build`.)
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host is required so Vite binds to 0.0.0.0 instead of localhost,
# otherwise the port won't be reachable from outside the container.
CMD ["npm", "run", "dev", "--", "--host"]