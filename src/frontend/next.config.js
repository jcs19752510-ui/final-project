/** @type {import('next').NextConfig} */
const nextConfig = {
  // 2026-09-18(Next.js 전환): Docker 프로덕션 이미지를 얇게 유지하기 위해
  // standalone 산출물을 사용한다 — `next start` 대신 `node
  // .next/standalone/server.js`로 구동(Dockerfile 참조). devDependencies
  // 없이도 실행 가능한 자체 완결 서버가 생성된다.
  output: "standalone",
};

// package.json에 "type": "module"이 있어 .js는 ESM으로 해석된다(CommonJS
// module.exports를 쓰면 빌드 자체가 실패함 — 실제로 겪고 수정).
export default nextConfig;
