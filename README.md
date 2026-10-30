# Cofa Codex 하네스

AI와 함께 업무 과제를 푸는 시간제한 평가(Cofa-Probe, 180분)를 위해 만든 **개인 준비용 Codex 작업 지침과 스킬**이다.
요구사항을 근거로 정의하고, 업무 담당자에게 확인하고, 작게 만들고, 실행 증거로 검증하고, 내가 설명할 수 있는 기록을 남기는 것을 돕는다.

주최사·운영사·OpenAI의 공식 자료가 아니며, 과제 README·과제 안내·응시 플랫폼의 공식 규칙이 항상 우선한다.

## 들어 있지 않은 것

- 과제 문제, 정답, 예상 답안, 과제별 구현 코드
- 응시 안내 원문, 접속 정보, 개인 정보, 실제 데이터
- 실행 스크립트(설치용 파일 복사 스크립트 제외), 외부 서비스·API 키·특정 모델 의존

이 저장소는 **작업 방식에 대한 지침과 빈 문서 양식만** 담는다. 실제 구현은 응시 환경 안에서 한다.

## 구성

```text
AGENTS.md                       작업 규칙 (응시 규칙 반영)
install.sh                      스킬·AGENTS.md 복사 (네트워크·설정 변경 없음)
skills/
  hx-analyze/                   초기 분석: 요구사항·현재 구현·테스트·불확실성 + 담당자 질문 초안
    templates/REQUIREMENTS.md
  hx-interview/                 담당자 질문 다듬기(check), 받은 답 기록(record)
  hx-plan/                      MVP·작업별 완료 기준·시간 기준 계획, 승인 후 진행
    templates/PLAN.md
    templates/DECISIONS.md
  hx-data/                      데이터 과제: 데이터 계약·점검·집계 함정·정직한 평가
  hx-debug/                     막혔을 때: 실패 신호 → 원인 가설 → 최소 수정 → 재검증, 10분 보고
  hx-verify/                    실행 증거로 검증, 통과·실패·미실행 구분
  hx-wrap/                      제출 확정 전 점검, 공유 메시지 초안, 이해도 점검
```

스킬은 모두 **직접 호출할 때만** 쓰이도록 설정했다(`$hx-analyze`처럼 부른다). 불필요한 자동 로딩으로 토큰을 쓰지 않기 위해서다.

## 반영한 응시 규칙

| 규칙 | 하네스의 처리 |
|---|---|
| 제공된 Codex·허용 모델만, 개인 API 키·외부 AI 금지, Codex 업데이트 금지 | AGENTS.md 4장에 명시 |
| 과제·결과물 외부 전송, git push, 업로드 금지 | 명시. 하네스 자체도 외부 통신 없음 |
| Computer Use·화면 자동 조작 금지 | 검증은 터미널 테스트·HTTP 요청, 화면 확인·메신저·제출은 사용자가 직접 |
| 감독·차단 우회, 플랫폼 설정·프로세스 변경 금지 | 명시. install.sh는 파일 복사만 함 |
| 공개 자료는 허용 경로로, 결과물 통째 대체 금지 | 명시. 출처 기록 |
| 토큰 사용량 참고 | 재읽기·반복 요청 금지, 스킬 직접 호출만 |
| 서버 0.0.0.0 바인딩, 플랫폼 Browser로 확인 | 명시 |
| 후속 서술형 AI 사용 금지 | 제출 확정 후에는 어떤 도움도 하지 않도록 명시. 이해도 점검은 확정 전에만, 모범 답안 없음 |

## 설치

과제 작업 폴더(Codex를 실행할 폴더)에서 실행한다. 키트는 작업 폴더 **밖**에 받는다.

```bash
git clone https://github.com/JINwonLEE/cofa-codex-harness /tmp/hx
bash /tmp/hx/install.sh
```

- 스킬은 `~/.agents/skills`에 설치되어 제출물에 섞이지 않는다. 작업 폴더에 넣고 싶으면 `--project`.
- 작업 폴더에 `AGENTS.md`가 없을 때만 복사한다. 이미 있으면 덮어쓰지 않고, Codex에 보낼 첫 메시지를 안내한다.
- Codex를 새로 실행하고 `/skills`에서 `hx-` 스킬 7개를 확인한다. 안 보이면 `bash /tmp/hx/install.sh --codex-home --no-agents` 후 재시작.
- `/tmp`에 쓸 수 없으면 `~/hx` 등 작업 폴더 밖 다른 경로를 쓴다.
- 플랫폼이 다른 스킬 적용 방법을 안내하면 그 방법을 따른다.

## 당일 흐름

| 단계 | 호출 | 결과 |
|---|---|---|
| 1. 초기 분석 (코드 수정 없음) | `$hx-analyze` | A~G 보고, REQUIREMENTS.md, 담당자 질문 초안 |
| 2. 담당자 확인 | `$hx-interview check` → 직접 전송 → `$hx-interview record` | 답변 기록, 요구·가정 갱신 |
| 3. 계획 | `$hx-plan` → 승인 | PLAN.md (MVP, 완료 기준, 시간 기준) |
| 4. 구현 | 작업 단위 위임 (데이터가 있으면 먼저 `$hx-data`) | 작업마다 결과·검증·다음 보고, 로컬 커밋 |
| 막혔을 때 | `$hx-debug` | 원인 확인 후 최소 수정, 10분 넘으면 선택지 보고 |
| 5. 검증 | `$hx-verify` | 통과·실패·미실행 표 |
| 6. 마무리 (확정 전) | `$hx-wrap` | 제출 준비 판정, README 결과 정리, 공유 메시지, 이해도 점검 |

첫 메시지 예:

```text
$hx-analyze 작업 시작 HH:MM, 마감 HH:MM이야. 과제를 분석해줘.
```

## 사전 체험에서 확인할 것

- `git clone`이 되는지, `/skills`에 스킬이 보이는지, `$hx-analyze` 호출이 되는지
- 간단한 서버를 `0.0.0.0`에 띄우고 플랫폼 Browser에서 열리는지

## 출처와 라이선스

MIT. 아래 MIT 공개 저장소의 아이디어를 참고해 새로 작성했고, 일부 문구 구조는 [NOTICE](NOTICE)에 고지했다.

- [ripplelover/cofa-ready-kit](https://github.com/ripplelover/cofa-ready-kit) — 요구사항→출처→확인 방법 연결, 큰 실패부터 검증, 확정 후 AI 중단, 반도체 데이터의 분모·재검사·조인 주의점
- [ColdTbrew/cofa-skills](https://github.com/ColdTbrew/cofa-skills) — 데이터 점검 목록, 누수·분할·기준선 중심의 정직한 평가
- [MunChanCHOI1/qualifier-skill](https://github.com/MunChanCHOI1/qualifier-skill) — 통과·실패·미실행 구분, 경계 조항
- [mattpocock/skills](https://github.com/mattpocock/skills) — 질문을 묶어 가설과 함께 묻는 방식
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — 완료 기준이 붙은 작은 작업 단위
- [obra/superpowers](https://github.com/obra/superpowers) — 실행 증거 없이 완료를 주장하지 않기, 원인 확인 전 수정 금지
- [mattpocock/skills](https://github.com/mattpocock/skills)의 diagnosing-bugs — 이 버그에서만 실패하는 신호부터 만들기

이 저장소는 사용한 평가의 결과 통지 전까지 공개 상태로 유지한다.
