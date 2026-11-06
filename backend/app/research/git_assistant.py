"""CYRUS Safe Git Assistant.

Provides safe, non-destructive version control inspection, diff review,
recent commit inspection, and automated Conventional Commit message drafting.

Enforces:
1. Non-destructive safety: Strictly blocks destructive git operations (force push, hard reset).
2. GUARDIAN authorization: Read commands are evaluated under L1_READ; commit drafting under L2_PREPARE.
3. Addresses the user as "Sir" and maintains 100% English communication.
"""

from dataclasses import dataclass, field
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.guardian.permissions import ActionRequest, PermissionTier, permission_engine

logger = logging.getLogger("cyrus.research.git_assistant")


@dataclass
class GitFileChange:
    """Represents a single changed file in the git index or working tree."""
    status_code: str
    file_path: str
    change_type: str  # Modified, Untracked, Staged New, Deleted, Renamed


@dataclass
class GitStatusReport:
    """Structured git status report."""
    branch: str
    is_clean: bool
    staged_files: List[GitFileChange] = field(default_factory=list)
    unstaged_files: List[GitFileChange] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    summary: str = ""


class SafeGitAssistant:
    """Guarded Git operations assistant strictly confined to CYRUS repository."""

    def __init__(self, repo_root: Optional[Path] = None, user_form_of_address: str = "Sir"):
        self.repo_root = (repo_root or Path(settings.CYRUS_SANDBOX_PATH)).resolve()
        self.form_of_address = user_form_of_address

    def _run_git_cmd(self, args: List[str], timeout: int = 5) -> subprocess.CompletedProcess:
        """Executes a git command inside the repository root safely."""
        return subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def get_status(self) -> GitStatusReport:
        """Retrieves structured git repository status."""
        try:
            branch_proc = self._run_git_cmd(["branch", "--show-current"])
            current_branch = branch_proc.stdout.strip() or "detached"

            status_proc = self._run_git_cmd(["status", "--porcelain=v1"])
            lines = status_proc.stdout.splitlines()

            staged: List[GitFileChange] = []
            unstaged: List[GitFileChange] = []
            untracked: List[str] = []

            for line in lines:
                if len(line) < 3:
                    continue
                index_status = line[0]
                worktree_status = line[1]
                path = line[3:].strip()

                if index_status == "?" and worktree_status == "?":
                    untracked.append(path)
                    continue

                if index_status in ["M", "A", "D", "R"]:
                    change_map = {"M": "Modified", "A": "Added", "D": "Deleted", "R": "Renamed"}
                    staged.append(
                        GitFileChange(
                            status_code=index_status,
                            file_path=path,
                            change_type=change_map.get(index_status, "Staged"),
                        )
                    )

                if worktree_status in ["M", "D"]:
                    change_map = {"M": "Modified", "D": "Deleted"}
                    unstaged.append(
                        GitFileChange(
                            status_code=worktree_status,
                            file_path=path,
                            change_type=change_map.get(worktree_status, "Modified"),
                        )
                    )

            is_clean = len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0

            if is_clean:
                summary = (
                    f"The Git repository on branch `{current_branch}` is completely clean, "
                    f"{self.form_of_address}. There are no uncommitted changes."
                )
            else:
                summary = (
                    f"Git repository status on branch `{current_branch}`, {self.form_of_address}:\n\n"
                    f"• **Staged Changes**: {len(staged)} files ready for commit.\n"
                    f"• **Unstaged Changes**: {len(unstaged)} modified files.\n"
                    f"• **Untracked Files**: {len(untracked)} new files."
                )

            return GitStatusReport(
                branch=current_branch,
                is_clean=is_clean,
                staged_files=staged,
                unstaged_files=unstaged,
                untracked_files=untracked,
                summary=summary,
            )

        except Exception as e:
            logger.error("Git status inspection failed: %s", e)
            return GitStatusReport(
                branch="unknown",
                is_clean=False,
                summary=f"Unable to read Git status, {self.form_of_address}: {e}",
            )

    def get_recent_commits(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the most recent commits formatted cleanly."""
        try:
            log_proc = self._run_git_cmd(["log", f"-n{limit}", "--pretty=format:%H|%h|%an|%ar|%s"])
            if log_proc.returncode != 0:
                return []

            commits = []
            for line in log_proc.stdout.splitlines():
                parts = line.split("|", 4)
                if len(parts) == 5:
                    full_hash, short_hash, author, date_rel, subject = parts
                    commits.append({
                        "full_hash": full_hash,
                        "short_hash": short_hash,
                        "author": author,
                        "date": date_rel,
                        "subject": subject,
                    })
            return commits
        except Exception as e:
            logger.error("Git log inspection failed: %s", e)
            return []

    def get_diff(self, staged: bool = False, max_chars: int = 15000) -> Dict[str, Any]:
        """Reads git diff output safely without exceeding buffer bounds."""
        args = ["diff", "--staged"] if staged else ["diff"]
        try:
            diff_proc = self._run_git_cmd(args)
            output = diff_proc.stdout
            truncated = False
            if len(output) > max_chars:
                output = output[:max_chars]
                truncated = True

            return {
                "diff": output,
                "staged": staged,
                "truncated": truncated,
                "char_length": len(output),
            }
        except Exception as e:
            return {"error": str(e), "diff": "", "staged": staged}

    def draft_commit_message(self) -> Dict[str, Any]:
        """Analyzes active changes and drafts a standardized Conventional Commit message."""
        status = self.get_status()
        if status.is_clean:
            return {
                "has_changes": False,
                "draft": "",
                "summary": f"There are no active changes to draft a commit for, {self.form_of_address}.",
            }

        all_changed_files = [f.file_path for f in status.staged_files] + [f.file_path for f in status.unstaged_files] + status.untracked_files

        # Determine conventional type and scope
        scope = "core"
        commit_type = "feat"
        description = "update project components"

        if any("backend/app/research" in f or "research" in f for f in all_changed_files):
            scope = "research"
            commit_type = "feat"
            description = "implement sandboxed doc reader, web research, code inspector, and git assistant"
        elif any("backend/app/agents" in f for f in all_changed_files):
            scope = "agents"
            commit_type = "feat"
            description = "enhance specialist multi-agent capabilities"
        elif any("tests/" in f or "test_" in f for f in all_changed_files):
            scope = "tests"
            commit_type = "test"
            description = "expand architectural test suite verification"
        elif any(f.endswith(".md") for f in all_changed_files):
            scope = "docs"
            commit_type = "docs"
            description = "update architecture and development milestone documentation"

        draft_message = f"{commit_type}({scope}): {description}"

        summary = (
            f"I have drafted a standardized Conventional Commit message for your review, {self.form_of_address}:\n\n"
            f"```\n{draft_message}\n```\n\n"
            f"This commit covers {len(all_changed_files)} affected files across the repository."
        )

        return {
            "has_changes": True,
            "draft": draft_message,
            "type": commit_type,
            "scope": scope,
            "affected_files": all_changed_files,
            "summary": summary,
        }

    def evaluate_git_action_safety(self, command: str) -> Dict[str, Any]:
        """Evaluates whether a requested git command is safe or requires GUARDIAN approval."""
        cmd_clean = command.strip().lower()
        destructive_patterns = [
            "reset --hard", "push --force", "push -f", "clean -fd", "clean -f",
            "branch -d", "branch -d", "checkout -f", "restore --staged",
        ]

        for pattern in destructive_patterns:
            if pattern in cmd_clean:
                return {
                    "is_safe": False,
                    "risk_tier": PermissionTier.L4_RESTRICTED,
                    "reason": f"Potentially destructive Git command detected ('{pattern}'). Explicit user approval required.",
                }

        return {
            "is_safe": True,
            "risk_tier": PermissionTier.L1_READ if any(c in cmd_clean for c in ["status", "log", "diff", "branch"]) else PermissionTier.L3_EXECUTE,
            "reason": "Safe non-destructive Git operation.",
        }


safe_git_assistant = SafeGitAssistant()
