# aimock 프론트엔드 (Next.js)

2026-09-18에 Vite/react-router-dom에서 Next.js(App Router)로 전환했다 —
근거는 `docs/adr/adr-003-data-stack.md`가 아니라 원본 계획서(§4.1)가
React/Next.js를 명시했던 것과의 아키텍처 정합을 사용자가 직접 요청한
것(대화 기록, 2026-09-18). 상세 이력은 저장소 루트 `CLAUDE.md` 작업
이력 참조.

## 개발

```bash
npm install
npm run dev       # http://localhost:3000
```

백엔드(`src/backend`)가 8000번 포트에서 떠 있어야 한다
(`docker compose up -d postgres redis app worker` 후
`docker exec <app 컨테이너> alembic upgrade head`).

## 빌드/프로덕션 확인

```bash
npm run build      # .next/standalone 산출물 생성
npm run start       # 로컬에서 standalone 산출물 실행
```

Docker: `docker compose --profile prod up -d frontend` (포트 8080).

## 디렉터리 구조

- `src/app/` — Next.js App Router 라우트 정의(파일 기반 라우팅). 각
  `page.tsx`는 `src/screens/`의 실제 UI 컴포넌트를 `ProtectedRoute`로
  감싸는 얇은 래퍼다.
- `src/screens/` — 실제 화면 컴포넌트(예전 `src/pages/`에서 이름 변경 —
  Next.js가 `pages/`를 레거시 Pages Router 예약 디렉터리로 자동 인식해
  타입 검증이 깨지는 충돌이 있어 `screens/`로 옮김).
- `src/components/`, `src/state/`, `src/api/` — 라우팅과 무관한 공용
  컴포넌트/상태/API 클라이언트, 전환 전과 동일 구조 유지.

## 테스트

```bash
npm run test   # vitest (next.config.js와 별도인 vitest.config.ts 사용)
npm run lint   # oxlint
```

## 환경변수

`NEXT_PUBLIC_API_BASE_URL` — 백엔드 API base URL(빌드 타임에 클라이언트
번들에 고정됨, Vite의 `VITE_API_BASE_URL`과 동일한 원리).
