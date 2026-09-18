/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 2026-09-18(Next.js 전환): 예전엔 vite.config.ts 하나가 개발 서버/빌드와
// vitest 설정을 겸했지만, 이제 개발 서버/빌드는 Next.js가 전담(next.config.js)
// 하고 이 파일은 vitest 전용으로 분리했다 — Next.js 공식 문서도 App Router
// 프로젝트에서 Vitest를 이렇게 별도 vite 설정으로 돌리는 방식을 권장한다.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
});
