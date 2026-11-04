#!/usr/bin/env python3
"""Project-local, offline installer. Python standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

BEGIN = b"<!-- cofa-codex-harness:begin -->"
END = b"<!-- cofa-codex-harness:end -->"
META = Path(".agents/cofa-codex-harness")
MANIFEST = META / "manifest.json"
SKILLS = ("hx-analyze", "hx-data", "hx-debug", "hx-design", "hx-explain", "hx-interview", "hx-plan", "hx-verify", "hx-wrap")


class InstallError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    """Reject symlinks (including dangling ones) and non-directory ancestors."""
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise InstallError("심볼릭 링크는 변경하지 않습니다: {}".format(path))
        if path != root / relative and path.exists() and not path.is_dir():
            raise InstallError("디렉터리가 아닌 경로: {}".format(path))
    if path.exists() and not path.is_file():
        raise InstallError("일반 파일이 아닌 경로: {}".format(path))
    return path


def read_optional(path):
    return path.read_bytes() if path.exists() else None


def managed_block(rules):
    heading = (
        "\n# Cofa Codex 하네스 (설치 관리 영역)\n\n"
        "이 블록 밖의 기존 프로젝트 지침과 과제·플랫폼 공식 규칙이 우선한다. "
        "이 블록은 보조 작업 규칙이며 시스템·개발자 지침을 변경하지 않는다.\n"
        "출처·라이선스: `.agents/cofa-codex-harness/NOTICE`, `.agents/cofa-codex-harness/LICENSE`.\n"
        "사용자 규칙은 이 블록 밖에 적는다. 세부 hx- 스킬은 직접 호출할 때만 쓴다.\n\n"
    ).encode("utf-8")
    return BEGIN + heading + rules.rstrip() + b"\n" + END


def merge_rules(original, block, old_hash):
    original = original or b""
    starts, ends = original.count(BEGIN), original.count(END)
    if starts == 0 and ends == 0:
        return original + (b"\n\n" if original else b"") + block + b"\n"
    if starts != 1 or ends != 1:
        raise InstallError("AGENTS 관리 표식이 중복되거나 불완전합니다. 기존 내용을 보존한 채 표식을 확인하세요.")
    start, end = original.index(BEGIN), original.index(END) + len(END)
    if start >= end - len(END):
        raise InstallError("AGENTS 관리 표식의 순서가 잘못되었습니다.")
    previous = original[start:end]
    if previous != block and digest(previous) != old_hash:
        raise InstallError("AGENTS 관리 블록이 직접 수정되었습니다. 사용자 규칙을 블록 밖에 보존하고 변경을 검토하세요.")
    return original[:start] + block + original[end:]


def writable(path):
    # Check mode bits as well as access(), so a root-run test still catches read-only files.
    if path.exists() and (not (path.stat().st_mode & 0o222) or not os.access(path, os.W_OK)):
        raise InstallError("쓰기 권한이 없습니다 (권한을 자동 변경하지 않음): {}".format(path))
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not (parent.stat().st_mode & 0o222) or not os.access(parent, os.W_OK | os.X_OK):
        raise InstallError("디렉터리에 쓰기 권한이 없습니다: {}".format(parent))
    if path.exists() and path.stat().st_nlink > 1:
        raise InstallError("하드 링크는 변경하지 않습니다: {}".format(path))


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".cofa-install-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(kit, work, check=False, no_agents=False):
    if work == kit or kit in work.parents or work in kit.parents:
        raise InstallError("키트는 과제 폴더 밖에 두고, 과제 루트에서 실행하세요.")

    state_path = safe_path(work, MANIFEST)
    state_bytes = read_optional(state_path)
    state = json.loads(state_bytes) if state_bytes is not None else {}
    if not isinstance(state, dict) or (state and state.get("version") != 1):
        raise InstallError("알 수 없는 설치 기록입니다: {}".format(state_path))
    old_files = state.get("files", {})
    if not isinstance(old_files, dict):
        raise InstallError("설치 기록의 files 형식이 잘못되었습니다.")

    desired = {}
    for name in SKILLS:
        source = kit / "skills" / name
        safe_path(kit, Path("skills") / name / "SKILL.md")
        if not (source / "SKILL.md").is_file():
            raise InstallError("키트 스킬이 누락되었습니다: {}".format(name))
        for file in sorted(source.rglob("*")):
            if file.is_symlink():
                raise InstallError("키트에 심볼릭 링크가 있습니다: {}".format(file))
            if file.is_file():
                desired[Path(".agents/skills") / name / file.relative_to(source)] = file.read_bytes()
    for name in ("LICENSE", "NOTICE"):
        desired[META / name] = safe_path(kit, Path(name)).read_bytes()

    snapshots = {state_path: state_bytes}
    for relative, data in desired.items():
        path = safe_path(work, relative)
        current = read_optional(path)
        snapshots[path] = current
        if current is not None and current != data and digest(current) != old_files.get(relative.as_posix()):
            raise InstallError("기존 파일과 충돌합니다 (덮어쓰지 않음): {}".format(path))
    # Unknown extra files are left alone; removed upstream files are never silently deleted.
    for relative in old_files.keys() - {str(p) for p in desired}:
        raise InstallError("이전 버전의 파일을 자동 삭제하지 않습니다. 먼저 검토하세요: {}".format(relative))

    active_name = state.get("agents_file")
    block_hash = state.get("block_sha256")
    if not no_agents:
        override = safe_path(work, Path("AGENTS.override.md"))
        base = safe_path(work, Path("AGENTS.md"))
        override_bytes = read_optional(override)
        # An empty override is not activated: doing so would hide an existing AGENTS.md.
        active = override if override_bytes and override_bytes.strip() else base
        if active_name and active_name != active.name:
            raise InstallError("적용되는 AGENTS 파일이 바뀌었습니다. 기존 관리 블록을 검토한 뒤 설치 기록과 함께 정리하세요.")
        active_name = active.name
        current = read_optional(active)
        try:
            (current or b"").decode("utf-8")
        except UnicodeDecodeError:
            raise InstallError("AGENTS 파일이 UTF-8이 아닙니다. 원본을 보존한 채 인코딩을 확인하세요.")
        block = managed_block(safe_path(kit, Path("AGENTS.md")).read_bytes())
        desired[Path(active_name)] = merge_rules(current, block, block_hash)
        snapshots[active] = current
        block_hash = digest(block)
        if len(desired[Path(active_name)]) > 32768:
            raise InstallError("AGENTS 파일이 32 KiB를 넘습니다. 지침 잘림을 피하도록 기존 문서를 먼저 검토하세요.")

    new_state = {
        "version": 1,
        "files": {p.as_posix(): digest(data) for p, data in desired.items() if p.name not in ("AGENTS.md", "AGENTS.override.md")},
        "agents_file": active_name,
        "block_sha256": block_hash,
    }
    desired[MANIFEST] = (json.dumps(new_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    changes = [(safe_path(work, p), data) for p, data in desired.items() if snapshots.get(work / p) != data]
    if check:
        if changes:
            raise InstallError("설치 확인 실패: 누락되거나 갱신이 필요한 파일 {}개. --check 없이 다시 실행하세요.".format(len(changes)))
        print("설치 확인 통과: 스킬 {}개·출처·설치 기록".format(len(SKILLS)) + (" (규칙 확인 제외)" if no_agents else "·자동 적용 규칙"))
        return

    # Validate all planned writes before changing anything. Do not chmod user files.
    for path, _ in changes:
        writable(path)
    for path, _ in changes:
        if read_optional(safe_path(work, path.relative_to(work))) != snapshots.get(path):
            raise InstallError("설치 중 파일이 바뀌었습니다. 다시 확인하세요: {}".format(path))
    # Each file replacement is atomic; permission errors/interruption are not a whole-tree transaction.
    for path, data in changes:
        atomic_write(path, data)
    print("설치 완료: {} (변경 {}개, 스킬 {}개)".format(work, len(changes), len(SKILLS)))
    if not no_agents:
        print("자동 규칙: {} — 기존 본문을 보존했습니다.".format(active_name))
    else:
        print("--no-agents: 자동 규칙을 설치/갱신하지 않았습니다.")
    print("같은 과제 루트에서 제공된 Codex를 새로 시작하고 /skills를 확인하세요.")
    check_args = "--check --no-agents" if no_agents else "--check"
    print("파일 설치 확인: install.sh {} (실제 Codex 로딩 확인은 별도)".format(check_args))


def main():
    if sys.version_info < (3, 8):
        print("Python 3.8+가 필요합니다.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="현재 과제 루트에 hx- 스킬 전체와 자동 작업 규칙을 설치합니다. 네트워크·설정 변경 없음.")
    parser.add_argument("--project", action="store_true", help="기본 동작과 같음 (이전 명령 호환)")
    parser.add_argument("--check", action="store_true", help="파일 설치 상태만 확인, 쓰기 없음")
    parser.add_argument("--no-agents", action="store_true", help="스킬·출처만 설치; 자동 규칙은 설치/갱신하지 않음")
    args = parser.parse_args()
    try:
        install(Path(__file__).resolve().parent.parent, Path.cwd().resolve(), args.check, args.no_agents)
    except (InstallError, OSError, ValueError) as error:
        print("중단: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
