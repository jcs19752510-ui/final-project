# 작업지시서 — U3-b(표정/음성운율 분석)

> `harness/harness_02_work_order_template.md` 형식.

## 문서 정보
- 프로젝트/단위: aimock / U3-b
- 참조 TRD: `docs/trd/aimock_u3b_trd.md`
- 작성일: 2026-09-08

## §0. 전제 조건
- 완료: U1-b(미디어 저장), U4(리포트 생성). Must-have 전체 완료 상태.
- 사용자가 실제 얼굴 영상(mp4)·음성(m4a) 샘플 제공(2026-09-08) — 로컬
  스크래치 경로에만 보관, 저장소에 커밋 안 함.

## §1. 이번 단계 범위
- [ ] `EmotionAnalyzer`/`ProsodyAnalyzer` 인터페이스 + 실제 구현
  (DeepFace/librosa) + Fake 구현
- [ ] `report_service.generate_report()`에 배선(미디어 있으면 분석,
  없으면 조용히 스킵)
- [ ] 실제 샘플로 수동 검증 + 합성 데이터로 pytest 자동화
- [ ] `requirements.txt`에 `deepface`, `librosa`, `opencv-python-headless`,
  `soundfile` 추가, Docker 이미지 재빌드 확인

## §2. 안 하는 것 (Out of Scope)
- 프론트엔드 실시간 웹캠 프레임 캡처 UI — 별도 규모의 작업이라 후속 과제.
- 감정/운율 결과를 리포트 요약 LLM 프롬프트에 자동 반영 — 원재료만 노출.
- 표정 변화를 시간축 그래프로 시각화하는 프론트엔드 UI — 이번엔 데이터만.

## §3. 착수 전 확정 정책
| 미결 항목 | 권장 기본값 | 이번 세션 적용 여부 |
|---|---|---|
| DeepFace 검출기 백엔드 | `opencv`(가장 가볍고 의존성 적음) | 적용 |
| 분석 실패 시 동작 | 예외 대신 폴백값 반환 | 적용 |

## §4. 완료 후 받을 결과물
- [ ] 소스 코드(`src/backend/app/ai/emotion.py`, `prosody.py`, `report_service.py` 수정)
- [ ] 테스트 결과(AC-1~5) → `내부테스트결과서/`
- [ ] 판단 근거 요약(A0 반영)

## §5. 프롬프트
> 작성 세션이 곧 실행 세션 — harness_04 절차 생략.

## §6. 다음 단계 예고
- 사람이 "실시간 웹캠 캡처 UI도 만들지" 결정 필요(TRD §7).
