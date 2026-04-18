# Frontend Dockerfile for Vue (multi-stage)
# Build stage
FROM node:20-alpine AS build

RUN mkdir -p /app && chown -R node:node /app
USER node

WORKDIR /app

COPY --chown=node:node package*.json ./
RUN npm ci --silent || npm install --legacy-peer-deps --silent

COPY --chown=node:node . .

RUN node_modules/.bin/vite build

# Production stage - serve built files with nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
