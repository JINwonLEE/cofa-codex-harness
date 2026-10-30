#!/usr/bin/env bash
# Cofa Codex 하네스 설치
#
# 사용법: 과제 작업 폴더(Codex를 실행할 폴더)에서 실행한다.
#   bash /tmp/hx/install.sh               스킬을 ~/.agents/skills에 설치하고,
#                                          작업 폴더에 AGENTS.md가 없을 때만 복사한다.
#   bash /tmp/hx/install.sh --project     스킬을 ./.agents/skills에 설치한다.
#   bash /tmp/hx/install.sh --codex-home  ${CODEX_HOME:-~/.codex}/skills에도 설치한다(스킬이 안 보일 때).
#   bash /tmp/hx/install.sh --no-agents   AGENTS.md를 복사하지 않는다.
#
# 이 스크립트는 파일 복사만 한다. 네트워크 접속, 작업 폴더의 git 조작, Codex·플랫폼 설정 변경을 하지 않는다.
# 이미 있는 파일·스킬 폴더는 덮어쓰지 않는다.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(pwd)"

if [ "$WORK" = "$KIT" ]; then
  echo "키트 폴더가 아니라 과제 작업 폴더에서 실행하세요." >&2
  exit 1
fi

project=0
codex_home=0
copy_agents=1
for arg in "$@"; do
  case "$arg" in
    --project)    project=1 ;;
    --codex-home) codex_home=1 ;;
    --no-agents)  copy_agents=0 ;;
    -h|--help)    sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "알 수 없는 옵션: $arg" >&2; exit 1 ;;
  esac
done

if [ "$project" -eq 1 ]; then
  targets=("$WORK/.agents/skills")
else
  targets=("$HOME/.agents/skills")
fi
if [ "$codex_home" -eq 1 ]; then
  targets+=("${CODEX_HOME:-$HOME/.codex}/skills")
fi

for target in "${targets[@]}"; do
  mkdir -p "$target"
  for dir in "$KIT"/skills/*/; do
    name="$(basename "$dir")"
    if [ -e "$target/$name" ]; then
      echo "건너뜀 (이미 있음): $target/$name"
    else
      cp -R "$dir" "$target/$name"
      echo "설치: $target/$name"
    fi
  done
done

if [ "$copy_agents" -eq 1 ]; then
  if [ -e "$WORK/AGENTS.md" ]; then
    echo
    echo "작업 폴더에 AGENTS.md가 이미 있어 그대로 두었습니다(과제 파일 보존)."
    echo "Codex 첫 메시지로 다음을 보내세요:"
    echo "  $KIT/AGENTS.md 를 읽고 이 세션의 추가 작업 규칙으로 따라줘. 작업 폴더의 AGENTS.md와 과제 안내가 우선이야."
  else
    cp "$KIT/AGENTS.md" "$WORK/AGENTS.md"
    echo "설치: $WORK/AGENTS.md"
  fi
fi

rev="$(git -C "$KIT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo
echo "완료 (키트 버전: $rev). Codex를 새로 실행한 뒤 /skills 에서 hx-로 시작하는 스킬 7개를 확인하세요."
echo "목록에 없으면: bash $KIT/install.sh --codex-home --no-agents 를 실행하고 Codex를 다시 시작하세요."
