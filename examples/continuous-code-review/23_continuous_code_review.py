#!/usr/bin/env python3
"""
Example 23: Continuous Code Review - Automated Reviews on Every Commit
========================================================================

AUDIENCE: Development teams wanting continuous quality feedback
VALUE: Catch issues early with automatic code review on every commit
PATTERN: Git hook integration, background execution, review management

INSPIRATION: This example is inspired by roborev (https://github.com/wesm/roborev)
but built using Amplifier's composable primitives for maximum flexibility.

What this demonstrates:
  - Installing git post-commit hooks
  - Triggering Amplifier sessions from git hooks
  - Background execution patterns
  - Review result management and viewing
  - Building roborev-like workflows with Amplifier

When you'd use this:
  - Continuous quality feedback during development
  - Catching issues while context is fresh
  - Team-wide code review standards
  - Pre-PR quality gates

Real-world use cases:
  - Solo developers: Get a second pair of eyes on every change
  - Teams: Enforce coding standards continuously
  - Open source: Maintain quality across many contributors
  - Learning: Get feedback on your code as you write it

TIME TO VALUE: 20 minutes
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier_foundation import Bundle
from amplifier_foundation import load_bundle

# =============================================================================
# SECTION 1: Git Hook Installation
# =============================================================================


class GitHookInstaller:
    """Install and manage git hooks for continuous code review."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.hooks_dir = repo_path / ".git" / "hooks"
        self.review_logs_dir = repo_path / ".amplifier" / "review-logs"

    def is_git_repo(self) -> bool:
        """Check if the directory is a git repository."""
        return (self.repo_path / ".git").exists()

    def install_post_commit_hook(self, review_bundle: str | None = None) -> bool:
        """Install a post-commit hook that triggers code review.

        Args:
            review_bundle: Optional path to custom review bundle
                          (uses foundation default if not provided)

        Returns:
            True if hook was installed successfully
        """
        if not self.is_git_repo():
            print(f"❌ ERROR: {self.repo_path} is not a git repository")
            return False

        # Create review logs directory
        self.review_logs_dir.mkdir(parents=True, exist_ok=True)

        # Create post-commit hook script
        hook_path = self.hooks_dir / "post-commit"

        # Build the review command
        if review_bundle:
            review_cmd = f'amplifier run --bundle "{review_bundle}" "Review commit $COMMIT_SHA"'
        else:
            review_cmd = 'amplifier run "Review the code changes in commit $COMMIT_SHA"'

        hook_content = f"""#!/bin/bash
# Amplifier Continuous Code Review Hook
# Auto-generated - edit with caution

COMMIT_SHA=$(git rev-parse HEAD)
REVIEW_LOG="{self.review_logs_dir}/$COMMIT_SHA.log"

echo "🔍 Code review queued for commit $COMMIT_SHA"

# Run review in background, log output
nohup bash -c '{review_cmd} 2>&1' > "$REVIEW_LOG" &

# Store PID for potential cleanup
echo $! > "{self.review_logs_dir}/.last_review_pid"
"""

        # Write hook file
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)  # Make executable

        print(f"✅ Post-commit hook installed at {hook_path}")
        print(f"📁 Review logs will be stored in {self.review_logs_dir}")
        return True

    def uninstall_post_commit_hook(self) -> bool:
        """Remove the post-commit hook."""
        hook_path = self.hooks_dir / "post-commit"

        if not hook_path.exists():
            print("ℹ️  No post-commit hook found")
            return False

        # Check if it's our hook
        content = hook_path.read_text()
        if "Amplifier Continuous Code Review Hook" in content:
            hook_path.unlink()
            print("✅ Post-commit hook removed")
            return True
        else:
            print("⚠️  Post-commit hook exists but wasn't created by Amplifier")
            print("   Not removing it to be safe")
            return False

    def list_reviews(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent code reviews.

        Args:
            limit: Maximum number of reviews to return

        Returns:
            List of review metadata dicts
        """
        if not self.review_logs_dir.exists():
            return []

        reviews = []
        for log_file in sorted(self.review_logs_dir.glob("*.log"), reverse=True)[:limit]:
            commit_sha = log_file.stem
            stat = log_file.stat()

            # Try to extract review summary from log
            try:
                content = log_file.read_text()
                # Look for common review indicators
                has_issues = any(word in content.lower() for word in ["issue", "problem", "bug", "fix", "improve"])
                lines = len(content.splitlines())
            except Exception:
                has_issues = False
                lines = 0

            reviews.append(
                {
                    "commit": commit_sha[:8],
                    "full_sha": commit_sha,
                    "timestamp": datetime.fromtimestamp(stat.st_mtime),
                    "log_file": log_file,
                    "size_bytes": stat.st_size,
                    "lines": lines,
                    "has_issues": has_issues,
                }
            )

        return reviews

    def show_review(self, commit_sha: str) -> str | None:
        """Show the review for a specific commit.

        Args:
            commit_sha: Full or short commit SHA

        Returns:
            Review content or None if not found
        """
        # Find log file (handles both short and full SHA)
        for log_file in self.review_logs_dir.glob(f"{commit_sha}*.log"):
            return log_file.read_text()

        return None


# =============================================================================
# SECTION 2: Review Dashboard
# =============================================================================


class ReviewDashboard:
    """Interactive dashboard for managing code reviews."""

    def __init__(self, installer: GitHookInstaller):
        self.installer = installer

    def display_summary(self):
        """Display a summary of recent reviews."""
        print("\n" + "=" * 80)
        print("🔍 CONTINUOUS CODE REVIEW DASHBOARD")
        print("=" * 80)

        reviews = self.installer.list_reviews(limit=10)

        if not reviews:
            print("\nℹ️  No reviews found yet. Make a commit to see reviews appear!")
            return

        print(f"\n📊 Recent Reviews ({len(reviews)} shown)")
        print("-" * 80)
        print(f"{'COMMIT':12} {'DATE':20} {'SIZE':10} {'STATUS':10}")
        print("-" * 80)

        for review in reviews:
            timestamp = review["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            size = f"{review['size_bytes']:,}B"
            status = "⚠️  Issues" if review["has_issues"] else "✅ Clean"

            print(f"{review['commit']:12} {timestamp:20} {size:10} {status:10}")

    def show_detailed_review(self, commit_sha: str):
        """Show detailed review for a commit."""
        content = self.installer.show_review(commit_sha)

        if content is None:
            print(f"\n❌ No review found for commit {commit_sha}")
            return

        print("\n" + "=" * 80)
        print(f"📝 REVIEW FOR COMMIT {commit_sha}")
        print("=" * 80)
        print(content)

    def get_statistics(self) -> dict[str, Any]:
        """Get review statistics."""
        reviews = self.installer.list_reviews(limit=100)

        if not reviews:
            return {"total": 0, "with_issues": 0, "clean": 0, "avg_size": 0}

        total = len(reviews)
        with_issues = sum(1 for r in reviews if r["has_issues"])
        clean = total - with_issues
        avg_size = sum(r["size_bytes"] for r in reviews) / total

        return {"total": total, "with_issues": with_issues, "clean": clean, "avg_size": int(avg_size)}


# =============================================================================
# SECTION 3: Demo Scenarios
# =============================================================================


async def scenario_install_hooks():
    """Scenario 1: Install git hooks for continuous review."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Install Continuous Review Hooks")
    print("=" * 80)
    print("\nThis will install a post-commit hook that automatically reviews")
    print("every commit in the background.")
    print("-" * 80)

    # Prompt for repository path
    repo_path = input("\nEnter path to git repository (or '.' for current): ").strip() or "."
    repo_path = Path(repo_path).resolve()

    installer = GitHookInstaller(repo_path)

    if not installer.is_git_repo():
        print(f"\n❌ ERROR: {repo_path} is not a git repository")
        print("\nTip: Navigate to a git repo or initialize one with 'git init'")
        return

    print(f"\n📂 Repository: {repo_path}")

    # Ask about custom bundle
    use_custom = input("\nUse custom review bundle? (y/N): ").strip().lower() == "y"
    custom_bundle = None

    if use_custom:
        custom_bundle = input("Enter bundle path: ").strip()
        if not Path(custom_bundle).exists():
            print(f"\n⚠️  Bundle not found: {custom_bundle}")
            print("Proceeding with default foundation bundle")
            custom_bundle = None

    # Install hook
    print("\n⏳ Installing post-commit hook...")
    success = installer.install_post_commit_hook(custom_bundle)

    if success:
        print("\n✅ SUCCESS! Continuous code review is now active.")
        print("\nWhat happens next:")
        print("  1. Every time you commit, a review is queued")
        print("  2. Reviews run in the background (won't block commits)")
        print("  3. Results are logged to .amplifier/review-logs/")
        print("\nTry it:")
        print(f"  cd {repo_path}")
        print("  git commit -m 'test: trigger review'")
        print(f"  python {Path(__file__).name}  # Run scenario 2 to see results")


async def scenario_view_reviews():
    """Scenario 2: View recent code reviews."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: View Code Reviews")
    print("=" * 80)
    print("\nView recent automated code reviews.")
    print("-" * 80)

    repo_path = input("\nEnter path to git repository (or '.' for current): ").strip() or "."
    repo_path = Path(repo_path).resolve()

    installer = GitHookInstaller(repo_path)
    dashboard = ReviewDashboard(installer)

    # Show summary
    dashboard.display_summary()

    # Show statistics
    stats = dashboard.get_statistics()
    if stats["total"] > 0:
        print("\n" + "=" * 80)
        print("📈 STATISTICS")
        print("=" * 80)
        print(f"  Total reviews:     {stats['total']}")
        print(f"  Reviews with issues: {stats['with_issues']} ({stats['with_issues']/stats['total']*100:.1f}%)")
        print(f"  Clean reviews:     {stats['clean']} ({stats['clean']/stats['total']*100:.1f}%)")
        print(f"  Avg review size:   {stats['avg_size']:,} bytes")

    # Option to view detailed review
    reviews = installer.list_reviews(limit=10)
    if reviews:
        print("\n" + "-" * 80)
        view_detail = input("\nView detailed review? Enter commit SHA (or press Enter to skip): ").strip()

        if view_detail:
            dashboard.show_detailed_review(view_detail)


async def scenario_uninstall_hooks():
    """Scenario 3: Uninstall hooks."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Uninstall Continuous Review Hooks")
    print("=" * 80)
    print("\nRemove the post-commit hook.")
    print("-" * 80)

    repo_path = input("\nEnter path to git repository (or '.' for current): ").strip() or "."
    repo_path = Path(repo_path).resolve()

    installer = GitHookInstaller(repo_path)

    confirm = input(f"\nRemove post-commit hook from {repo_path}? (y/N): ").strip().lower()

    if confirm == "y":
        installer.uninstall_post_commit_hook()
    else:
        print("\nℹ️  Cancelled")


async def scenario_manual_review():
    """Scenario 4: Manually trigger a review (no git hook required)."""
    print("\n" + "=" * 80)
    print("SCENARIO 4: Manual Code Review")
    print("=" * 80)
    print("\nTrigger a code review without installing git hooks.")
    print("Useful for trying out the review workflow.")
    print("-" * 80)

    # Get commit or file to review
    target = input("\nWhat to review? (commit SHA, file path, or 'last' for last commit): ").strip() or "last"

    # Load foundation bundle
    foundation_path = Path(__file__).parent.parent
    foundation = await load_bundle(str(foundation_path))

    print("\n⏳ Preparing review session...")
    prepared = await foundation.prepare()
    session = await prepared.create_session()

    # Build review prompt based on target
    if target == "last":
        prompt = """Review the changes in the most recent git commit.

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Security concerns
4. Suggestions for improvement

Be thorough but concise."""
    elif target.startswith("/") or target.startswith("."):
        prompt = f"""Review the code in file: {target}

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Security concerns
4. Suggestions for improvement

Be thorough but concise."""
    else:
        prompt = f"""Review the changes in git commit: {target}

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Security concerns
4. Suggestions for improvement

Be thorough but concise."""

    print("\n🔍 Running code review...")
    print("-" * 80)

    try:
        async with session:
            response = await session.execute(prompt)

            print("\n" + "=" * 80)
            print("📝 REVIEW RESULTS")
            print("=" * 80)
            print(response)

            # Offer to save
            save = input("\n\nSave review to file? (y/N): ").strip().lower() == "y"
            if save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = Path(f"review_{timestamp}.txt")
                output_file.write_text(response)
                print(f"\n✅ Review saved to {output_file}")

    except Exception as e:
        print(f"\n❌ ERROR during review: {e}")


# =============================================================================
# SECTION 4: Interactive Menu
# =============================================================================


async def main():
    """Run interactive demonstration."""
    print("\n" + "=" * 80)
    print("🔍 Amplifier Continuous Code Review")
    print("=" * 80)
    print("\nVALUE: Automatic code review on every commit")
    print("INSPIRED BY: roborev (https://github.com/wesm/roborev)")
    print("BUILT WITH: Amplifier's composable primitives")
    print("\nWhat this enables:")
    print("  ✅ Continuous feedback during development")
    print("  ✅ Catch issues while context is fresh")
    print("  ✅ Team-wide quality standards")
    print("  ✅ Non-blocking background execution")

    scenarios = [
        ("Install Git Hooks", scenario_install_hooks),
        ("View Code Reviews", scenario_view_reviews),
        ("Uninstall Git Hooks", scenario_uninstall_hooks),
        ("Manual Review (No Hooks)", scenario_manual_review),
    ]

    print("\n" + "=" * 80)
    print("Choose a scenario:")
    print("=" * 80)
    for i, (name, _) in enumerate(scenarios, 1):
        print(f"  {i}. {name}")
    print("  q. Quit")
    print("-" * 80)

    choice = input("\nYour choice: ").strip().lower()

    if choice == "q":
        print("\n👋 Goodbye!")
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(scenarios):
            _, scenario_func = scenarios[idx]
            await scenario_func()
        else:
            print("\n❌ Invalid choice")
    except ValueError:
        print("\n❌ Invalid choice")

    print("\n" + "=" * 80)
    print("💡 KEY TAKEAWAYS")
    print("=" * 80)
    print("""
1. **Git Hook Integration**: Seamless automation via post-commit hooks
2. **Background Execution**: Reviews don't block commits
3. **Flexible Workflows**: Use default or custom review bundles
4. **Review Management**: Dashboard for viewing results and statistics

**Comparison to roborev:**
- Roborev: Fixed Go binary, daemon architecture, TUI
- Amplifier: Composable primitives, flexible workflows, session-based
- You get: More customization, multi-agent reviews, ecosystem integration

**Next steps:**
- Customize review criteria in your bundle
- Add specialized reviewers (security, performance, style)
- Build team-specific review dashboards
- Create recipes for complex review workflows

**Advanced patterns:**
- Multi-agent reviews (architect + security + performance)
- Conditional reviews (only for certain file types)
- Review aggregation across branches
- Integration with PR workflows
""")


if __name__ == "__main__":
    asyncio.run(main())
