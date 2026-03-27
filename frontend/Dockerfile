FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_BACKEND_URL=

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
