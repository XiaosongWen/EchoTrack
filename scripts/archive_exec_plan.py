#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def extract_issue_numbers(branch="", title="", body="", explicit_issue=None):
    issues = set()
    if explicit_issue:
        # e.g. "100" or "issue-100"
        m = re.search(r"(\d+)", str(explicit_issue))
        if m:
            issues.add(m.group(1))

    # Match in branch name, e.g. feature/77-supabase, issue-100, 100-fix
    if branch:
        branch_matches = re.findall(r"(?:^|/|-|_)(?:issue[-_]?)?(\d+)(?:[-_/]|$)", branch, re.IGNORECASE)
        for num in branch_matches:
            issues.add(num)

    # Match in PR title, e.g. "feat: something (#100)" or "issue-100"
    if title:
        title_matches = re.findall(r"(?:#|issue[-_\s]|issue#)(\d+)", title, re.IGNORECASE)
        for num in title_matches:
            issues.add(num)

    # Match in PR body, e.g. "Closes #100", "Fixes #100", "issue-100"
    if body:
        body_matches = re.findall(r"(?:closes|fixes|resolves|issue)[-_\s:#]*(\d+)", body, re.IGNORECASE)
        for num in body_matches:
            issues.add(num)

    return sorted(list(issues), key=lambda x: int(x))


def archive_exec_plans(repo_root: Path, issue_numbers: list[str], dry_run: bool = False):
    active_dir = repo_root / "agents" / "exec-plan" / "active"
    complete_dir = repo_root / "agents" / "exec-plan" / "complete"

    if not active_dir.exists():
        print(f"Active directory {active_dir} does not exist.")
        return []

    complete_dir.mkdir(parents=True, exist_ok=True)
    moved_items = []

    for issue in issue_numbers:
        # Match patterns like issue-100*, issue_100*, issue100*
        prefix_pattern = re.compile(rf"^issue[-_]?{issue}(?:[-_].*)?$", re.IGNORECASE)

        for item in active_dir.iterdir():
            if item.name == ".gitkeep":
                continue

            # Check if name matches prefix pattern (with or without .md extension)
            stem_or_name = item.stem if item.is_file() else item.name
            if prefix_pattern.match(stem_or_name) or prefix_pattern.match(item.name):
                dest = complete_dir / item.name
                print(f"Found matching item: {item} -> {dest}")
                moved_items.append((item, dest))

    if not moved_items:
        print(f"No active execution plans found for issue(s): {issue_numbers}")
        return []

    if dry_run:
        print("Dry run enabled; skipping move.")
        return moved_items

    for src, dst in moved_items:
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        
        # Try git mv first, fallback to shutil.move
        try:
            subprocess.run(["git", "mv", str(src), str(dst)], check=True, cwd=repo_root)
            print(f"git mv: {src.name} -> {dst}")
        except Exception:
            shutil.move(str(src), str(dst))
            print(f"shutil.move: {src.name} -> {dst}")

    return moved_items


def main():
    parser = argparse.ArgumentParser(description="Archive execution plans matching issue number.")
    parser.add_argument("--issue", help="Explicit issue number (e.g. 100)")
    parser.add_argument("--branch", default="", help="Git branch name")
    parser.add_argument("--title", default="", help="PR title")
    parser.add_argument("--body", default="", help="PR body")
    parser.add_argument("--repo-root", default=".", help="Root directory of the repository")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without moving")

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    issues = extract_issue_numbers(
        branch=args.branch,
        title=args.title,
        body=args.body,
        explicit_issue=args.issue,
    )

    print(f"Detected issue numbers: {issues}")
    if not issues:
        print("No issue number could be determined.")
        sys.exit(0)

    moved = archive_exec_plans(repo_root, issues, dry_run=args.dry_run)
    if moved:
        print(f"Successfully archived {len(moved)} item(s).")
    else:
        print("Nothing to archive.")


if __name__ == "__main__":
    main()
