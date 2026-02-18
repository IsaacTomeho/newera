from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".rb",
    ".rs",
    ".php",
    ".cs",
}

SECURITY_KEYWORDS = {
    "auth",
    "token",
    "secret",
    "key",
    "payment",
    "crypto",
    "wallet",
    "session",
    "permission",
    "policy",
}


@dataclass
class FileRisk:
    path: str
    lines_added: int
    lines_removed: int
    missing_tests: bool
    complexity_spike: bool
    security_sensitive: bool
    high_churn: bool

    @property
    def lines_changed(self) -> int:
        return self.lines_added + self.lines_removed


def _run_git(repo: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git command failed: {' '.join(args)}")
    return proc.stdout


def _safe_run_git(repo: Path, args: list[str]) -> str:
    try:
        return _run_git(repo, args)
    except RuntimeError:
        return ""


def _discover_changed_files(repo: Path, base: str, head: str) -> dict[str, tuple[int, int]]:
    numstat = _safe_run_git(repo, ["diff", "--numstat", f"{base}...{head}"])
    if not numstat.strip():
        numstat = _safe_run_git(repo, ["show", "--numstat", "--pretty=", head])

    changed: dict[str, tuple[int, int]] = {}
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        if added == "-" or removed == "-":
            # Skip binary files.
            continue
        try:
            changed[path] = (int(added), int(removed))
        except ValueError:
            continue
    return changed


def _repo_files(repo: Path) -> set[str]:
    out = _safe_run_git(repo, ["ls-files"])
    return {line.strip() for line in out.splitlines() if line.strip()}


def _is_code_file(path: Path) -> bool:
    return path.suffix in CODE_EXTENSIONS


def _likely_test_paths(path: Path) -> set[str]:
    stem = path.stem
    parent = path.parent
    ext = path.suffix
    candidates = {
        str(parent / f"test_{stem}{ext}"),
        str(parent / f"{stem}.test{ext}"),
        str(parent / f"{stem}.spec{ext}"),
        str(Path("tests") / f"test_{stem}{ext}"),
    }
    return candidates


def _read_file(repo: Path, file_path: str) -> str:
    full = repo / file_path
    if not full.exists() or not full.is_file():
        return ""
    try:
        return full.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _complexity_spike(text: str, changed_lines: int) -> bool:
    if not text:
        return False
    line_count = len(text.splitlines())
    function_count = len(re.findall(r"\b(def|function|func)\b", text))
    return line_count > 280 or function_count > 20 or changed_lines > 220


def _security_sensitive(path: str, text: str) -> bool:
    lowered = f"{path}\n{text[:5000]}".lower()
    return any(keyword in lowered for keyword in SECURITY_KEYWORDS)


def _high_churn(repo: Path, file_path: str) -> bool:
    out = _safe_run_git(repo, ["log", "--since=90.days", "--oneline", "--", file_path])
    commit_count = len([line for line in out.splitlines() if line.strip()])
    return commit_count >= 6


def _missing_tests(file_path: Path, tracked_files: set[str]) -> bool:
    if "test" in file_path.name.lower() or "spec" in file_path.name.lower():
        return False
    return not any(candidate in tracked_files for candidate in _likely_test_paths(file_path))


def _risk_tier(score: int) -> str:
    if score >= 80:
        return "Low"
    if score >= 60:
        return "Medium"
    return "High"


def _gate(score: int) -> str:
    if score < 50:
        return "Block"
    if score < 75:
        return "Review required"
    return "Pass"


def analyze_diff(repo_path: str, base: str = "HEAD~1", head: str = "HEAD") -> dict:
    repo = Path(repo_path).resolve()
    changed = _discover_changed_files(repo, base, head)
    tracked = _repo_files(repo)

    risks: list[FileRisk] = []
    for file_path, (added, removed) in changed.items():
        p = Path(file_path)
        if not _is_code_file(p):
            continue

        text = _read_file(repo, file_path)
        lines_changed = added + removed
        risks.append(
            FileRisk(
                path=file_path,
                lines_added=added,
                lines_removed=removed,
                missing_tests=_missing_tests(p, tracked),
                complexity_spike=_complexity_spike(text, lines_changed),
                security_sensitive=_security_sensitive(file_path, text),
                high_churn=_high_churn(repo, file_path),
            )
        )

    total_changed_lines = sum(item.lines_changed for item in risks)
    penalty = 0
    penalty += min(40, sum(20 for item in risks if item.missing_tests))
    penalty += min(30, sum(15 for item in risks if item.complexity_spike))
    penalty += min(20, sum(10 for item in risks if item.security_sensitive))
    penalty += min(20, sum(10 for item in risks if item.high_churn))
    penalty += min(20, total_changed_lines // 180 * 5)

    score = max(0, 100 - penalty)

    findings: list[str] = []
    if any(r.missing_tests for r in risks):
        findings.append("Test coverage gap")
    if any(r.complexity_spike for r in risks):
        findings.append("Complexity spike")
    if any(r.security_sensitive for r in risks):
        findings.append("Security-sensitive change")
    if any(r.high_churn for r in risks):
        findings.append("High-churn module touched")

    suggestions = _build_suggestions(risks)

    return {
        "repo": repo.name,
        "base": base,
        "head": head,
        "overall_trust_score": score,
        "risk_tier": _risk_tier(score),
        "gate_decision": _gate(score),
        "files_analyzed": len(risks),
        "total_lines_changed": total_changed_lines,
        "risk_drivers": findings,
        "suggested_test_additions": suggestions,
        "files": [
            {
                "path": r.path,
                "lines_added": r.lines_added,
                "lines_removed": r.lines_removed,
                "missing_tests": r.missing_tests,
                "complexity_spike": r.complexity_spike,
                "security_sensitive": r.security_sensitive,
                "high_churn": r.high_churn,
            }
            for r in risks
        ],
    }


def _build_suggestions(risks: Iterable[FileRisk]) -> list[str]:
    suggestions: list[str] = []
    for item in risks:
        if item.missing_tests:
            suggestions.append(f"Add unit tests for {item.path} covering success and failure paths.")
        if item.security_sensitive:
            suggestions.append(
                f"Add negative-path tests for auth/permission handling in {item.path}."
            )
        if item.complexity_spike:
            suggestions.append(
                f"Add regression test cases for edge branches introduced in {item.path}."
            )
    if not suggestions:
        suggestions.append("No urgent additions detected. Keep baseline smoke tests on this PR.")
    return suggestions[:6]


def generate_markdown_report(result: dict) -> str:
    lines = [
        "# MergeGuard Verification Report",
        "",
        "## Pull Request Context",
        f"- Repo: {result['repo']}",
        f"- Diff range: {result['base']}...{result['head']}",
        f"- Files analyzed: {result['files_analyzed']}",
        f"- Total lines changed (code files): {result['total_lines_changed']}",
        "",
        "## Trust Score",
        f"- Overall trust score (0-100): {result['overall_trust_score']}",
        f"- Risk tier: {result['risk_tier']}",
        f"- Gate decision: {result['gate_decision']}",
        "",
        "## Risk Drivers",
    ]

    if result["risk_drivers"]:
        lines.extend(f"- {driver}" for driver in result["risk_drivers"])
    else:
        lines.append("- No dominant risk drivers detected.")

    lines.extend(["", "## Suggested Test Additions"])
    lines.extend(f"- {item}" for item in result["suggested_test_additions"])

    lines.extend(["", "## File-Level Findings"])
    for file_result in result["files"]:
        flags = []
        if file_result["missing_tests"]:
            flags.append("missing-tests")
        if file_result["complexity_spike"]:
            flags.append("complexity")
        if file_result["security_sensitive"]:
            flags.append("security")
        if file_result["high_churn"]:
            flags.append("high-churn")
        flag_text = ", ".join(flags) if flags else "none"
        lines.append(
            f"- `{file_result['path']}` (+{file_result['lines_added']}/-{file_result['lines_removed']}) flags: {flag_text}"
        )

    return "\n".join(lines) + "\n"


def serialize_json(result: dict) -> str:
    return json.dumps(result, indent=2, sort_keys=True) + "\n"
