from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_diff, generate_markdown_report, serialize_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MergeGuard: AI code verification report generator")
    parser.add_argument("--repo", default=".", help="Path to target git repository")
    parser.add_argument("--base", default="HEAD~1", help="Base git ref for diff")
    parser.add_argument("--head", default="HEAD", help="Head git ref for diff")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (default: mergeguard-report.md or mergeguard-report.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze_diff(args.repo, base=args.base, head=args.head)

    if args.format == "json":
        rendered = serialize_json(result)
        output = Path(args.output or "mergeguard-report.json")
    else:
        rendered = generate_markdown_report(result)
        output = Path(args.output or "mergeguard-report.md")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"MergeGuard report written to {output}")
    print(
        f"Trust score: {result['overall_trust_score']} | Risk tier: {result['risk_tier']} | Gate: {result['gate_decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
