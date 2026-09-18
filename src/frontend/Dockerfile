# 프로덕션 빌드 서빙용(2026-09-08 추가, 2026-09-18 Next.js 전환으로 nginx
# 정적 서빙에서 Node 서버 구동으로 교체). 개발은 여전히 `npm run dev`
# (포트 3000)를 씀 — 이 이미지는 `docker compose --profile prod up` 등으로
# 실제 프로덕션 빌드를 확인하고 싶을 때만 사용.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# 빌드 시점에 API base URL을 고정(Next.js는 NEXT_PUBLIC_ 접두사 env를
# 빌드 타임에 클라이언트 번들에 굽는다 — Vite의 VITE_ 접두사와 동일 원리).
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

# standalone 산출물만 옮겨 이미지를 얇게 유지(node_modules 전체 불필요).
FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
