"""Offline installer regression tests; no Codex, Git, network, or third-party packages."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_install", ROOT / "scripts/install.py")
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cofa install test ")
        self.root = Path(self.temporary.name)
        self.kit = self.root / "kit with spaces"
        self.project = self.root / "task with spaces"
        self.kit.mkdir()
        self.project.mkdir()
        for name in ("AGENTS.md", "LICENSE", "NOTICE", "install.sh"):
            shutil.copy2(ROOT / name, self.kit / name)
        for name in ("skills", "scripts"):
            shutil.copytree(ROOT / name, self.kit / name, ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        # Restore fixture permissions, never permissions outside the temporary tree.
        for path in self.root.rglob("*"):
            if not path.is_symlink():
                path.chmod(0o700 if path.is_dir() else 0o600)
        self.temporary.cleanup()

    def install(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return INSTALLER.install(self.kit, self.project, **kwargs)

    def cli(self, *args, cwd=None):
        env = dict(os.environ, HOME=str(self.root / "home"), CODEX_HOME=str(self.root / "codex home"))
        return subprocess.run(
            ["bash", str(self.kit / "install.sh"), *args],
            cwd=cwd or self.project, env=env, text=True, capture_output=True, check=False,
        )

    def snapshot(self):
        result = {}
        for path in [self.project, *sorted(self.project.rglob("*"))]:
            info = path.lstat()
            value = os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
            result[str(path.relative_to(self.project))] = (info.st_mode, info.st_mtime_ns, value)
        return result

    def assert_rejected_without_changes(self, **kwargs):
        before = self.snapshot()
        with self.assertRaises(INSTALLER.InstallError):
            self.install(**kwargs)
        self.assertEqual(before, self.snapshot())

    def skill(self, name="hx-analyze"):
        return self.project / ".agents/skills" / name / "SKILL.md"

    def test_fresh_cli_install_is_project_local(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        skills = self.project / ".agents/skills"
        self.assertEqual({p.name for p in skills.iterdir()}, set(INSTALLER.SKILLS))
        for name in INSTALLER.SKILLS:
            self.assertEqual(self.skill(name).read_bytes(), (self.kit / "skills" / name / "SKILL.md").read_bytes())
        for name in ("LICENSE", "NOTICE"):
            self.assertEqual((self.project / INSTALLER.META / name).read_bytes(), (self.kit / name).read_bytes())
        rules = (self.project / "AGENTS.md").read_bytes()
        self.assertEqual(rules.count(INSTALLER.BEGIN), 1)
        self.assertEqual(rules.count(INSTALLER.END), 1)
        self.assertIn((self.kit / "AGENTS.md").read_bytes().rstrip(), rules)
        manifest = json.loads((self.project / INSTALLER.MANIFEST).read_text())
        self.assertEqual(manifest["agents_file"], "AGENTS.md")
        self.assertFalse((self.root / "home").exists())
        self.assertFalse((self.root / "codex home").exists())

    def test_bundled_rules_copy_matches_agents(self):
        self.assertEqual((ROOT / "skills/hx-analyze/RULES.md").read_bytes(), (ROOT / "AGENTS.md").read_bytes())

    def test_user_scope_installs_only_under_home(self):
        agents = self.project / "AGENTS.md"
        agents.write_bytes(b"# platform rules\n")
        agents.chmod(0o444)
        self.project.chmod(0o555)
        before = self.snapshot()
        result = self.cli("--user")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, self.snapshot())
        home = self.root / "home"
        skills = home / ".agents/skills"
        self.assertEqual({p.name for p in skills.iterdir()}, set(INSTALLER.SKILLS))
        for name in INSTALLER.SKILLS:
            self.assertEqual((skills / name / "SKILL.md").read_bytes(), (self.kit / "skills" / name / "SKILL.md").read_bytes())
        self.assertEqual((skills / "hx-analyze/RULES.md").read_bytes(), (self.kit / "AGENTS.md").read_bytes())
        self.assertTrue((home / INSTALLER.MANIFEST).is_file())
        self.assertFalse((home / "AGENTS.md").exists())
        self.assertFalse((self.root / "codex home").exists())
        result = self.cli("--check", "--user")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--check --user", self.cli("--user").stdout)

    def test_user_scope_rejects_kit_inside_home_agents_and_project_flag(self):
        self.assertNotEqual(self.cli("--user", "--project").returncode, 0)
        inside = self.root / "home/.agents/kit"
        shutil.copytree(self.kit, inside)
        result = subprocess.run(["bash", str(inside / "install.sh"), "--user"], cwd=self.project,
                                env=dict(os.environ, HOME=str(self.root / "home")), text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "home/.agents/skills").exists())

    def test_install_preserves_codex_configuration_auth_and_version_files(self):
        protected = []
        for folder in (self.root / "home/.codex", self.root / "codex home"):
            folder.mkdir(parents=True)
            for name in ("config.toml", "auth.json", "version.json"):
                file = folder / name
                file.write_bytes(b"fixture: must not change\n")
                protected.append(file)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in protected}
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in protected})

    def test_reinstall_does_not_rewrite_files_or_duplicate_rules(self):
        self.install()
        before = self.snapshot()
        self.install()
        self.assertEqual(before, self.snapshot())

    def test_preserves_original_bytes_and_later_user_suffix(self):
        agents = self.project / "AGENTS.md"
        original = "# 기존 규칙\r\n원래 지침을 보존한다.".encode("utf-8")
        agents.write_bytes(original)
        agents.chmod(0o600)
        self.install()
        block = INSTALLER.managed_block((self.kit / "AGENTS.md").read_bytes())
        self.assertEqual(agents.read_bytes(), original + b"\n\n" + block + b"\n")
        self.assertEqual(stat.S_IMODE(agents.stat().st_mode), 0o600)
        suffix = b"\n# User-added rule outside the block\n"
        agents.write_bytes(agents.read_bytes() + suffix)
        before = agents.read_bytes()
        self.install()
        self.assertEqual(agents.read_bytes(), before)

    def test_existing_nonempty_override_receives_rules(self):
        base = self.project / "AGENTS.md"
        override = self.project / "AGENTS.override.md"
        base.write_bytes(b"# Base project rules\n")
        override.write_bytes(b"# Active override\n")
        original_base = base.read_bytes()
        self.install()
        self.assertEqual(base.read_bytes(), original_base)
        self.assertTrue(override.read_bytes().startswith(b"# Active override\n"))
        self.assertIn(INSTALLER.BEGIN, override.read_bytes())
        self.install(check=True)

    def test_empty_override_does_not_shadow_existing_base(self):
        override = self.project / "AGENTS.override.md"
        override.write_bytes(b" \n\t")
        (self.project / "AGENTS.md").write_bytes(b"# Existing base\n")
        self.install()
        self.assertEqual(override.read_bytes(), b" \n\t")
        self.assertIn(INSTALLER.BEGIN, (self.project / "AGENTS.md").read_bytes())

    def test_malformed_or_duplicate_markers_are_not_overwritten(self):
        for data in (
            INSTALLER.BEGIN,
            INSTALLER.END,
            INSTALLER.END + b"\n" + INSTALLER.BEGIN,
            INSTALLER.BEGIN + INSTALLER.BEGIN + INSTALLER.END,
            INSTALLER.BEGIN + INSTALLER.END + INSTALLER.END,
        ):
            with self.subTest(data=data):
                (self.project / "AGENTS.md").write_bytes(data)
                self.assert_rejected_without_changes()

    def test_existing_conflicting_skill_stops_before_any_writes(self):
        existing = self.skill("hx-wrap")
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b"user-owned skill\n")
        self.assert_rejected_without_changes()

    def test_existing_identical_skill_can_be_adopted(self):
        existing = self.skill()
        existing.parent.mkdir(parents=True)
        existing.write_bytes((self.kit / "skills/hx-analyze/SKILL.md").read_bytes())
        self.install()
        self.install(check=True)

    def test_managed_upgrade_changes_only_unedited_installed_content(self):
        agents = self.project / "AGENTS.md"
        agents.write_bytes(b"# Project rules\n")
        self.install()
        agents.write_bytes(agents.read_bytes() + b"\n# User suffix\n")
        source_skill = self.kit / "skills/hx-analyze/SKILL.md"
        source_skill.write_bytes(source_skill.read_bytes() + b"\nUpdated harness skill.\n")
        source_rules = self.kit / "AGENTS.md"
        source_rules.write_bytes(source_rules.read_bytes() + b"\nUpdated harness rule.\n")
        self.install()
        self.assertEqual(self.skill().read_bytes(), source_skill.read_bytes())
        self.assertTrue(agents.read_bytes().startswith(b"# Project rules\n\n"))
        self.assertTrue(agents.read_bytes().endswith(b"\n# User suffix\n"))
        self.assertIn(b"Updated harness rule.", agents.read_bytes())
        self.install(check=True)

    def test_locally_edited_skill_is_not_overwritten(self):
        self.install()
        self.skill().write_bytes(self.skill().read_bytes() + b"\nUser edit.\n")
        self.assert_rejected_without_changes()

    def test_locally_edited_managed_block_is_not_overwritten(self):
        self.install()
        agents = self.project / "AGENTS.md"
        agents.write_bytes(agents.read_bytes().replace(INSTALLER.END, b"User edit.\n" + INSTALLER.END))
        self.assert_rejected_without_changes()

    def test_check_never_writes_and_reports_missing_installation(self):
        self.assert_rejected_without_changes(check=True)
        self.install()
        before = self.snapshot()
        self.install(check=True)
        self.assertEqual(before, self.snapshot())
        self.skill().unlink()
        self.assert_rejected_without_changes(check=True)

    def test_check_detects_an_upstream_update_without_writing(self):
        self.install()
        source = self.kit / "skills/hx-analyze/SKILL.md"
        source.write_bytes(source.read_bytes() + b"\nNew version.\n")
        self.assert_rejected_without_changes(check=True)

    def test_no_agents_installs_only_skills_and_attribution(self):
        self.install(no_agents=True)
        self.assertFalse((self.project / "AGENTS.md").exists())
        self.assertFalse((self.project / "AGENTS.override.md").exists())
        self.install(check=True, no_agents=True)
        self.assert_rejected_without_changes(check=True)
        self.install()
        self.install(check=True)

    def test_no_agents_leaves_existing_rule_file_untouched(self):
        agents = self.project / "AGENTS.md"
        agents.write_bytes(b"# User-owned instructions\n")
        before = agents.stat().st_mtime_ns
        self.install(no_agents=True)
        self.assertEqual(agents.read_bytes(), b"# User-owned instructions\n")
        self.assertEqual(agents.stat().st_mtime_ns, before)

    def test_symlinked_agents_directory_does_not_write_outside_project(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / ".agents").symlink_to(outside, target_is_directory=True)
        self.assert_rejected_without_changes()
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_rule_file_does_not_modify_target(self):
        outside = self.root / "external-rules.md"
        outside.write_bytes(b"external rules\n")
        (self.project / "AGENTS.md").symlink_to(outside)
        self.assert_rejected_without_changes()
        self.assertEqual(outside.read_bytes(), b"external rules\n")

    def test_dangling_symlink_is_rejected(self):
        outside = self.root / "not-created"
        (self.project / "AGENTS.override.md").symlink_to(outside)
        self.assert_rejected_without_changes()
        self.assertFalse(outside.exists())

    def test_symlinked_skill_file_is_rejected(self):
        outside = self.root / "external-skill.md"
        outside.write_bytes(b"external skill\n")
        skill = self.skill()
        skill.parent.mkdir(parents=True)
        skill.symlink_to(outside)
        self.assert_rejected_without_changes()
        self.assertEqual(outside.read_bytes(), b"external skill\n")

    def test_read_only_rules_file_stops_before_any_writes(self):
        agents = self.project / "AGENTS.md"
        agents.write_bytes(b"read-only project rules\n")
        agents.chmod(0o400)
        self.assert_rejected_without_changes()

    def test_read_only_target_directory_stops_before_any_writes(self):
        folder = self.project / ".agents"
        folder.mkdir()
        folder.chmod(0o500)
        self.assert_rejected_without_changes()

    def test_hard_linked_rule_file_is_not_modified(self):
        outside = self.root / "external-rules.md"
        outside.write_bytes(b"hard-linked rules\n")
        os.link(outside, self.project / "AGENTS.md")
        self.assert_rejected_without_changes()
        self.assertEqual(outside.read_bytes(), b"hard-linked rules\n")

    def test_unknown_flag_and_legacy_codex_home_fail_without_writes(self):
        for flag in ("--unknown", "--codex-home"):
            with self.subTest(flag=flag):
                before = self.snapshot()
                result = self.cli(flag)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(before, self.snapshot())

    def test_project_flag_is_compatible_with_default(self):
        self.assertEqual(self.cli("--project").returncode, 0)
        self.assertEqual(self.cli("--check").returncode, 0)

    def test_running_in_kit_or_with_kit_inside_project_is_rejected(self):
        result = self.cli(cwd=self.kit)
        self.assertNotEqual(result.returncode, 0)
        nested = self.kit / "nested"
        nested.mkdir()
        result = self.cli(cwd=nested)
        self.assertNotEqual(result.returncode, 0)
        result = self.cli(cwd=self.root)
        self.assertNotEqual(result.returncode, 0)

    def test_active_guidance_file_change_requires_review(self):
        self.install()
        (self.project / "AGENTS.override.md").write_bytes(b"new project override\n")
        self.assert_rejected_without_changes()

    def test_oversized_guidance_is_rejected_before_writes(self):
        (self.project / "AGENTS.md").write_bytes(b"x" * 32768)
        self.assert_rejected_without_changes()

    def test_missing_kit_skill_is_rejected_before_writes(self):
        (self.kit / "skills/hx-wrap/SKILL.md").unlink()
        self.assert_rejected_without_changes()

    def test_symlinked_source_skill_directories_are_rejected(self):
        for relative in ("skills", "skills/hx-analyze"):
            with self.subTest(relative=relative):
                source = self.kit / relative
                outside = self.root / "external-source-directory"
                source.rename(outside)
                source.symlink_to(outside, target_is_directory=True)
                self.assert_rejected_without_changes()
                source.unlink()
                outside.rename(source)

    def test_symlinked_source_rules_and_attribution_are_rejected(self):
        for name in ("AGENTS.md", "LICENSE", "NOTICE"):
            with self.subTest(name=name):
                source = self.kit / name
                original = source.read_bytes()
                outside = self.root / ("external-" + name)
                source.rename(outside)
                source.symlink_to(outside)
                self.assert_rejected_without_changes()
                self.assertEqual(outside.read_bytes(), original)
                source.unlink()
                outside.rename(source)

    def test_utf16_active_guidance_is_rejected_without_writes(self):
        for name in ("AGENTS.md", "AGENTS.override.md"):
            with self.subTest(name=name):
                agents = self.project / name
                agents.write_bytes("# 기존 사용자 규칙\n".encode("utf-16"))
                before = self.snapshot()
                result = self.cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(before, self.snapshot())
                agents.unlink()

    def test_no_agents_completion_shows_matching_check_command(self):
        result = self.cli("--no-agents")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--check --no-agents", result.stdout)

    def test_unrelated_files_are_not_removed(self):
        self.install()
        custom = self.skill().parent / "my-notes.txt"
        custom.write_bytes(b"personal notes\n")
        self.install()
        self.assertEqual(custom.read_bytes(), b"personal notes\n")


if __name__ == "__main__":
    unittest.main()
