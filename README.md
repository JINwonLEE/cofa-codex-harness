# Cofa Codex 하네스

AI와 함께 업무 과제를 푸는 시간제한 평가(Cofa-Probe, 180분)를 위해 만든 **개인 준비용 Codex 작업 지침과 스킬**이다.
요구사항을 근거로 정의하고, 업무 담당자에게 확인하고, 작게 만들고, 실행 증거로 검증하고, 내가 설명할 수 있는 기록을 남기는 것을 돕는다.

주최사·운영사·OpenAI의 공식 자료가 아니며, 과제 README·과제 안내·응시 플랫폼의 공식 규칙이 항상 우선한다.

## 가장 쉬운 설치: Codex에게 이 한 줄만

**사용할 과제 폴더를 열어 둔 제공된 Codex**에 다음처럼 말한다. 터미널 명령을 직접 입력할 필요는 없다.

> JINwonLEE/cofa-codex-harness 스킬 설치해줘.

이 요청을 받은 Codex는 아래 절차로 **9개 스킬 + 자동 작업 규칙을 함께 설치하고 확인**한다. 완료 후 사용자가 **같은 과제 폴더에서 새 대화 세션**을 열면 `$hx-analyze`부터 사용할 수 있다. 이미 열린 대화에 규칙을 다시 붙여 넣거나 앱을 업데이트하지 않는다. 플랫폼 권한·호환성 때문에 막히면 성공으로 보고하지 않고 원인을 알린다.

### Codex가 수행할 설치 절차

이 절차는 **설치 요청을 받은 에이전트용**이다. 사용자에게 명령 실행을 떠넘기지 말고, 허용된 터미널 도구로 아래 설치와 검증까지 수행한다. 일반 스킬 다운로더로 `skills/`만 복사하면 자동 작업 규칙이 빠지므로 **이 저장소의 `install.sh`를 사용한다.**

1. **clone 전에 설치 대상을 확정한다.** 현재 열려 있는 사용자의 과제/작업 루트 절대경로를 확인해 `TASK_ROOT`에 저장한다. 하네스 소스 폴더·홈·임시 다운로드 폴더를 과제 루트로 추측하지 않는다. 대상이 분명하면 재질문하지 않고, 알 수 없으면 사용할 폴더만 묻는다. 대상의 기존 `AGENTS.md`·`AGENTS.override.md`와 공식 안내를 먼저 읽는다.
2. Bash·Git·Python 3.8+와 허용된 다운로드 경로를 확인한다. 과제 **밖의 새 임시 디렉터리**에 공개 저장소를 clone한다. 기존 키트나 사용자 파일을 지우거나 덮어쓰지 않는다. 예시(에이전트가 `TASK_ROOT`를 실제 확인한 절대경로로 먼저 설정):

   ```bash
   KIT_PARENT="$(mktemp -d /tmp/cofa-codex-harness.XXXXXX)" &&
   git clone --depth 1 https://github.com/JINwonLEE/cofa-codex-harness "$KIT_PARENT/kit"
   ```

   `/tmp`가 허용되지 않거나 과제 폴더 안이면 허용된 **과제 밖** 위치를 쓴다. 다운로드 실패 시 중단한다. 이후 명령에서도 확인한 `TASK_ROOT`와 `KIT_PARENT` 절대경로를 유지한다(터미널 호출마다 셸이 새로 뜨면 변수를 다시 설정).
3. 내려받은 키트의 `README.md`, `install.sh`, `scripts/install.py`를 읽는다. 설치 범위가 프로젝트 파일뿐임을 확인한 뒤 **명시적으로 과제 루트로 이동해서** 설치와 검증을 순서대로 실행한다:

   ```bash
   (cd -- "$TASK_ROOT" &&
     bash "$KIT_PARENT/kit/install.sh" &&
     bash "$KIT_PARENT/kit/install.sh" --check)
   ```

4. 두 명령 모두 성공했을 때만 **설치한 과제 경로, 스킬 9개, 자동 규칙 파일, 파일 검증 통과**를 짧게 보고한다. 스킬은 `hx-analyze`, `hx-interview`, `hx-plan`, `hx-design`, `hx-data`, `hx-debug`, `hx-verify`, `hx-explain`, `hx-wrap`이다. 충돌·권한·의존성 문제가 나면 기존 파일과 설정을 보존하고 정확한 차단 원인만 알린다. 전역 설치로 우회하지 않는다.
5. 마지막으로 **“같은 과제 폴더에서 새 대화를 열고 `$hx-analyze`를 사용하세요.”**라고 안내한다. 새 세션을 UI 자동화로 열거나 Codex를 업데이트하거나 모델·provider·인증·`config.toml`·승인·샌드박스·네트워크·플랫폼 설정을 바꾸지 않는다. 스킬이 보이지 않는 문제도 이 설정을 바꿔 해결하지 말고 중단·보고한다. 실제 새 세션에서의 로딩까지 시험하지 않았다면 그렇게 명시한다. 설치 요청만으로 과제 분석·구현을 시작하지 않는다.

수동 설치를 원하는 경우에만 아래 [터미널 설치 안내](#설치--과제-루트에서-한-번)를 따른다.

## 들어 있지 않은 것

- 과제 문제, 정답, 예상 답안, 과제별 구현 코드
- 응시 안내 원문, 접속 정보, 개인 정보, 실제 데이터
- 과제 실행 스크립트(하네스의 로컬 설치·설치 테스트 제외), 외부 서비스·API 키·특정 모델 의존

이 저장소는 **작업 방식에 대한 지침·빈 문서 양식과 그 설치 도구**를 담는다. 실제 구현은 응시 환경 안에서 한다.

## 구성

```text
AGENTS.md                       작업 규칙 (응시 규칙 반영)
install.sh                      과제 폴더에 설치하는 진입점
scripts/install.py              스킬 복사·규칙 블록 관리·설치 확인 (Python 표준 라이브러리)
tests/test_install.py           임시 폴더에서만 도는 오프라인 설치 회귀 테스트
skills/
  hx-analyze/                   초기 분석: 요구사항·현재 구현·테스트·불확실성·핵심 기능 후보 + 담당자 질문 초안
    templates/REQUIREMENTS.md
  hx-interview/                 담당자 질문 다듬기(check), 받은 답 기록(record)
  hx-plan/                      MVP·작업별 완료 기준·시간 기준 계획, 승인 후 진행
    templates/PLAN.md
    templates/DECISIONS.md
  hx-design/                    핵심 로직 설계: 선택지·트레이드오프·판별 사례 비교, 사용자 결정 기록
  hx-data/                      데이터 과제: 데이터 계약·점검·집계 함정·정직한 평가
  hx-debug/                     막혔을 때: 실패 신호 → 원인 가설 → 최소 수정 → 재검증, 10분 보고
  hx-verify/                    실행 증거로 검증, 통과·실패·미실행 구분
  hx-explain/                   구현 지도·결정 카드·코드 근거 예상 질문으로 설명 연습 (모범 답안 없음)
  hx-wrap/                      제출 확정 전 점검, 공유 메시지 초안, 이해도 점검
```

**기본 작업 규칙은 자동 적용**, 9개 세부 스킬은 **직접 호출할 때만** 읽는다(`$hx-analyze`처럼 부른다). 매번 “하네스 규칙을 읽어줘”라고 말할 필요는 없다. 모든 스킬 본문을 매 세션 한꺼번에 넣지는 않는다.

## 반영한 응시 규칙

| 규칙 | 하네스의 처리 |
|---|---|
| 제공된 Codex·허용 모델만, 개인 API 키·외부 AI 금지, Codex 업데이트 금지 | AGENTS.md 4장에 명시 |
| 과제·결과물 외부 전송, git push, 업로드 금지 | 명시. 하네스 자체도 외부 통신 없음 |
| Computer Use·화면 자동 조작 금지 | 검증은 터미널 테스트·HTTP 요청, 화면 확인·메신저·제출은 사용자가 직접 |
| 감독·차단 우회, 플랫폼 설정·프로세스 변경 금지 | 명시. 설치기는 프로젝트 파일만 쓰며 설정은 건드리지 않음 |
| 공개 자료는 허용 경로로, 결과물 통째 대체 금지 | 명시. 출처 기록 |
| 토큰 사용량 참고 | 재읽기·반복 요청 금지, 스킬 직접 호출만 |
| 후속 서술형이 구체적인 기술 선택을 물음 | 핵심 로직은 사용자가 고르고 DECISIONS.md에 이유·대안·판별 사례를 남김(`$hx-design`), 사람 개입 기록, 제출 전 구현 지도·결정 카드로 설명 연습(`$hx-explain`) |
| 서버 0.0.0.0 바인딩, 플랫폼 Browser로 확인 | 명시 |
| 후속 서술형 AI 사용 금지 | 제출 확정 후에는 어떤 도움도 하지 않도록 명시. 이해도 점검은 확정 전에만, 모범 답안 없음 |

## 설치 — 과제 루트에서 한 번

필요한 것: **Bash, Python 3.8+**, 처음 내려받을 때만 Git. 패키지 추가 설치는 없다.
플랫폼이 하네스 사용·파일 추가를 허용하는지 먼저 확인한다. 아래 코드는 **과제 작업 폴더(제공된 Codex를 시작할 루트)**의 터미널에 붙여 넣는다. 키트 폴더로 `cd`하지 않는다.

```bash
git clone --depth 1 https://github.com/JINwonLEE/cofa-codex-harness /tmp/cofa-codex-harness && bash /tmp/cofa-codex-harness/install.sh
```

이미 `/tmp/cofa-codex-harness`에 이 키트를 받아 두었다면 다시 clone하지 않고 아래 **한 줄만** 실행한다. 다른 위치에 받았다면 실제 키트 경로로 바꾼다.

```bash
bash /tmp/cofa-codex-harness/install.sh
```

`clone`이 실패하면 `&&` 뒤 설치는 실행되지 않는다. 같은 이름의 폴더가 다른 용도라면 지우거나 덮어쓰지 말고, 과제 폴더 **밖의 새 경로**를 선택해 두 경로를 함께 바꾼다. `/tmp`가 막혀 있으면 허용된 외부 경로를 사용한다. 설치기는 내려받은 키트만 읽으며 네트워크·Git 명령을 실행하지 않는다.

### 설치되는 것 / 보존되는 것

- **현재 폴더에만** `.agents/skills/hx-*` 9개를 설치한다. 홈 디렉터리나 `~/.codex`에는 쓰지 않는다. `--project`는 같은 동작의 호환 옵션이다.
- `AGENTS.md`에 시작/끝 표식이 있는 **관리 블록으로 규칙 전체를 추가**한다. 기존 본문은 그대로 남고, 기존 프로젝트 지침·과제·플랫폼 공식 규칙이 하네스보다 우선한다.
- 내용 있는 `AGENTS.override.md`가 있으면 Codex가 그 파일을 우선하므로 **그 파일에만** 추가한다. 비어 있는 override는 활성화하지 않고 `AGENTS.md`를 사용한다. 하위 폴더의 별도 지침도 계속 존중한다.
- `.agents/cofa-codex-harness/`에 `LICENSE`, `NOTICE`, 설치 파일 해시 기록을 둔다. 키트 폴더를 나중에 지워도 설치한 규칙·스킬은 남는다.
- 재실행해도 블록이 중복되지 않는다. 설치기가 만든 부분만 갱신하며, 직접 수정한 스킬·관리 블록이나 동명의 다른 파일과 충돌하면 **덮어쓰지 않고 중단**한다. 사용자 규칙은 관리 블록 **밖에** 적는다.
- 심볼릭 링크·하드 링크·쓰기 권한 제한을 우회하지 않는다. 충돌·일반적인 권한 문제는 쓰기 전 확인한다. 파일별 교체는 원자적이지만 갑작스러운 중단·디스크 오류에 대한 전체 설치 롤백은 아니다. 실패하면 원인을 확인하고 재실행/검증한다.
- `.agents/`는 이제 과제 폴더 안에 있다. 제출 대상은 공식 안내대로 판단하고, `git add .`로 설치 파일까지 무심코 스테이징하지 않는다. 설치기가 `.gitignore`·Git 설정을 바꾸거나 커밋·push하지는 않는다.

### 설치 확인 (파일 확인과 실제 로딩을 구분)

같은 과제 루트에서:

```bash
bash /tmp/cofa-codex-harness/install.sh --check
```

이 명령은 **쓰기 없이** 스킬 9개·출처·관리 블록·설치 기록을 확인한다. 다음으로 제공된 Codex를 **같은 폴더에서 새로 시작**하고:

1. `/skills`에서 `hx-` 스킬 9개가 보이는지 확인한다.
2. “현재 읽은 프로젝트 지침 파일과 하네스 작업 순서를 짧게 알려줘”로 규칙 로딩을 확인한다.
3. `$hx-analyze`를 호출한다. 규칙을 수동으로 다시 주입할 필요는 없다.

공식 Codex의 [AGENTS.md 탐색 규칙](https://learn.chatgpt.com/docs/agent-configuration/agents-md)과 [프로젝트 스킬 경로](https://learn.chatgpt.com/docs/build-skills)에 맞춘 파일 설치다. **Cofa에 실제 제공되는 버전의 로딩은 사전 체험에서 확인해야 한다.** 이미 열린 세션에는 소급 적용되지 않으며, 설치기의 32 KiB 검사는 현재 파일만 대상으로 하므로, 상위 지침과 합친 크기 제한이나 플랫폼의 별도 로딩 정책 때문에 잘릴 수도 있다. 파일 확인 통과만으로 실제 로딩 성공을 주장하지 않는다.

안 보이더라도 Codex를 업데이트하거나 모델·provider·인증·`config.toml`·승인·샌드박스·네트워크·플랫폼 설정을 바꾸지 않는다. 스킬이 보이지 않는 문제도 이 설정을 바꿔 해결하지 말고 중단·보고한다. 기존 전역 설치(`~/.agents/skills`, `~/.codex/skills`)가 있으면 같은 이름이 중복될 수 있으므로 **본인이 설치한 사본인지 확인한 뒤** 정리 여부를 결정한다. 이 설치기는 전역 파일을 삭제하지 않으며, 중복 복사를 유도하던 `--codex-home` 옵션은 지원하지 않는다. 플랫폼 공식 안내가 우선이다.

`--no-agents`는 스킬·출처만 설치하는 선택 옵션이며 **자동 규칙 설치/갱신을 끈다**. 기존 블록을 제거하지는 않는다. 이 경우 확인도 `--check --no-agents`로 한다.

### 설치기 자체 테스트 (개발/사전 준비용)

키트 폴더에서 다음을 실행한다. 임시 폴더를 사용하며 실제 과제·홈 디렉터리를 설치 대상으로 쓰지 않는다. 네트워크·UI 자동화·AI 호출이 없다.

```bash
bash -n install.sh
python3 -m unittest discover -s tests -v
```

## 당일 흐름

| 단계 | 호출 | 결과 |
|---|---|---|
| 1. 초기 분석 (코드 수정 없음) | `$hx-analyze` | A~H 보고, 핵심 기능 후보·대표 흐름(확정·추정), REQUIREMENTS.md, 담당자 질문 초안(추정이면 1순위로 핵심 기능 확인) |
| 2. 담당자 확인 | `$hx-interview check` → 직접 전송 → `$hx-interview record` | 답변 기록, 요구·가정 갱신 |
| 3. 계획 | `$hx-plan` → 승인 | PLAN.md (MVP, 완료 기준, 시간 기준) |
| 4. 설계 (핵심 로직 작업마다) | `$hx-design` → 선택 | 선택지 표, 판별 사례, DECISIONS.md 결정 기록 |
| 5. 구현 | 작업 단위 위임 (데이터가 있으면 먼저 `$hx-data`) | 작업마다 결과·검증·다음 보고, 로컬 커밋 |
| 막혔을 때 | `$hx-debug` | 원인 확인 후 최소 수정, 10분 넘으면 선택지 보고 |
| 6. 검증 | `$hx-verify` | 통과·실패·미실행 표, 설계 판별 사례 테스트 |
| 7. 설명 준비 (마감 15~20분 전) | `$hx-explain` | 구현 지도, 결정 카드, 코드 근거 질문 연습 |
| 8. 마무리 (확정 전) | `$hx-wrap` | 제출 준비 판정, README 결과 정리, 공유 메시지, 기록 누락 확인 |

첫 메시지 예:

```text
$hx-analyze 작업 시작 HH:MM, 마감 HH:MM이야. 과제를 분석해줘.
```

## 사전 체험에서 확인할 것

- `git clone`과 `install.sh --check`가 되는지, 새 Codex 세션에 관리 블록 규칙과 `/skills`의 9개 스킬이 보이는지, `$hx-analyze` 호출이 되는지
- 간단한 서버를 `0.0.0.0`에 띄우고 플랫폼 Browser에서 열리는지

## 출처와 라이선스

MIT. 아래 MIT 공개 저장소의 아이디어를 참고해 새로 작성했고, 일부 문구 구조는 [NOTICE](NOTICE)에 고지했다.

- [ripplelover/cofa-ready-kit](https://github.com/ripplelover/cofa-ready-kit) — 요구사항→출처→확인 방법 연결, 큰 실패부터 검증, 확정 후 AI 중단, 반도체 데이터의 분모·재검사·조인 주의점
- [ColdTbrew/cofa-skills](https://github.com/ColdTbrew/cofa-skills) — 데이터 점검 목록, 누수·분할·기준선 중심의 정직한 평가
- [MunChanCHOI1/qualifier-skill](https://github.com/MunChanCHOI1/qualifier-skill) — 통과·실패·미실행 구분, 경계 조항
- [mattpocock/skills](https://github.com/mattpocock/skills) — 질문을 묶어 가설과 함께 묻는 방식
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — 완료 기준이 붙은 작은 작업 단위
- [obra/superpowers](https://github.com/obra/superpowers) — 실행 증거 없이 완료를 주장하지 않기, 원인 확인 전 수정 금지
- [bladem0117/cofa-kit](https://github.com/bladem0117/cofa-kit) — 사람 개입(AI 제안 수정·거절) 기록, 결정 지점별 질문 관점, 약점→영향→다음 계획 순서
- [CLM-BONNY/cofa-exam-harness](https://github.com/CLM-BONNY/cofa-exam-harness) — 기능별 입력→진입점→처리→저장→출력 구현 설명
- [gxonu/sk-probe-kit](https://github.com/gxonu/sk-probe-kit) — 선택·구조·범위·예외·검증 관점의 코드 근거 질문 (아이디어만 참고, 문구 미사용)
- [mattpocock/skills](https://github.com/mattpocock/skills)의 diagnosing-bugs — 이 버그에서만 실패하는 신호부터 만들기

## 버전

- `v1-qualifier2` (`be55d34`): 2차 예선(2026-10-31)에 사용한 버전. 같은 버전이 필요하면 `git -C /tmp/cofa-codex-harness checkout -q v1-qualifier2`.
- main: 이후 개선(설치기, `hx-design`, `hx-explain`, 사람 개입 기록 등).

이 저장소는 사용한 평가의 결과 통지 전까지 공개 상태로 유지한다.
