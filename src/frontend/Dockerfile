# 프로덕션 빌드 서빙용(2026-09-08 추가). 개발은 여전히 `npm run dev`(포트
# 5173)를 씀 — 이 이미지는 `docker compose --profile prod up` 등으로 실제
# 정적 빌드를 확인하고 싶을 때만 사용.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# 빌드 시점에 API base URL을 고정(Vite는 빌드 타임에 env를 번들에 굽는다).
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
