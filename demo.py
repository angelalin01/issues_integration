#!/usr/bin/env python3

import asyncio
from datetime import datetime
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from models import GitHubIssue, IssueState, IssueScopeResult, TaskCompletionResult, ConfidenceLevel

console = Console()

class DemoData:
    """Demo data for testing without real API keys"""

    @staticmethod
    def get_sample_issues() -> List[GitHubIssue]:
        """Generate sample GitHub issues for demo"""
        return [
            GitHubIssue(
                number=123,
                title="Add user authentication to login page",
                body="We need to implement OAuth2 authentication for the login page. Users should be able to login with GitHub, Google, or email/password.",
                state=IssueState.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                labels=["enhancement", "authentication", "frontend"],
                assignees=["developer1"],
                url="https://github.com/example/repo/issues/123",
                repository="example/repo"
            ),
            GitHubIssue(
                number=124,
                title="Fix memory leak in data processing pipeline",
                body="The data processing pipeline is consuming too much memory and causing OOM errors in production. Need to investigate and fix.",
                state=IssueState.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                labels=["bug", "performance", "backend"],
                assignees=["developer2"],
                url="https://github.com/example/repo/issues/124",
                repository="example/repo"
            ),
            GitHubIssue(
                number=125,
                title="Update documentation for API endpoints",
                body="The API documentation is outdated and missing several new endpoints. Need to update with current API spec.",
                state=IssueState.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                labels=["documentation"],
                assignees=[],
                url="https://github.com/example/repo/issues/125",
                repository="example/repo"
            ),
            GitHubIssue(
                number=126,
                title="Implement dark mode toggle",
                body="Add a dark mode toggle to the UI. Should persist user preference and apply to all pages.",
                state=IssueState.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                labels=["enhancement", "ui", "frontend"],
                assignees=["designer1"],
                url="https://github.com/example/repo/issues/126",
                repository="example/repo"
            ),
            GitHubIssue(
                number=127,
                title="Database migration script fails on PostgreSQL 14",
                body="The migration script works on PostgreSQL 13 but fails on version 14 due to syntax changes. Need to update for compatibility.",
                state=IssueState.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                labels=["bug", "database", "migration"],
                assignees=["dba1"],
                url="https://github.com/example/repo/issues/127",
                repository="example/repo"
            )
        ]

    @staticmethod
    def get_sample_scope_result(issue_number: int) -> IssueScopeResult:
        """Generate sample scoping result based on issue number"""
        scope_data = {
            123: {
                "confidence_score": 0.85,
                "confidence_level": ConfidenceLevel.HIGH,
                "complexity_assessment": "Medium complexity - requires OAuth integration and frontend changes",
                "estimated_effort": "3-5 days",
                "required_skills": ["React/Frontend", "OAuth2", "Authentication", "API Integration"],
                "action_plan": [
                    "Research OAuth2 providers (GitHub, Google)",
                    "Set up OAuth2 configuration",
                    "Implement login components",
                    "Add authentication middleware",
                    "Update user session management",
                    "Add logout functionality",
                    "Write tests for auth flow"
                ],
                "risks": ["OAuth provider rate limits", "Session management complexity", "Security vulnerabilities"]
            },
            124: {
                "confidence_score": 0.65,
                "confidence_level": ConfidenceLevel.MEDIUM,
                "complexity_assessment": "High complexity - requires deep debugging and performance optimization",
                "estimated_effort": "1-2 weeks",
                "required_skills": ["Python", "Memory Profiling", "Performance Optimization", "System Architecture"],
                "action_plan": [
                    "Profile memory usage in pipeline",
                    "Identify memory leak sources",
                    "Implement memory-efficient data structures",
                    "Add memory monitoring",
                    "Optimize garbage collection",
                    "Add memory usage alerts",
                    "Load test the fixes"
                ],
                "risks": ["Complex debugging required", "Production impact during testing", "May require architecture changes"]
            },
            125: {
                "confidence_score": 0.95,
                "confidence_level": ConfidenceLevel.HIGH,
                "complexity_assessment": "Low complexity - straightforward documentation update",
                "estimated_effort": "1-2 days",
                "required_skills": ["Technical Writing", "API Documentation", "OpenAPI/Swagger"],
                "action_plan": [
                    "Audit current API endpoints",
                    "Compare with existing documentation",
                    "Update API documentation",
                    "Add examples for new endpoints",
                    "Review and validate documentation",
                    "Deploy updated docs"
                ],
                "risks": ["Missing endpoint details", "Outdated examples"]
            },
            126: {
                "confidence_score": 0.80,
                "confidence_level": ConfidenceLevel.HIGH,
                "complexity_assessment": "Medium complexity - UI changes across multiple components",
                "estimated_effort": "2-3 days",
                "required_skills": ["CSS", "JavaScript", "UI/UX", "Local Storage"],
                "action_plan": [
                    "Design dark mode color scheme",
                    "Implement theme toggle component",
                    "Update CSS variables for theming",
                    "Add theme persistence logic",
                    "Update all UI components",
                    "Test across different browsers",
                    "Add accessibility considerations"
                ],
                "risks": ["Color contrast issues", "Component styling conflicts", "Browser compatibility"]
            },
            127: {
                "confidence_score": 0.70,
                "confidence_level": ConfidenceLevel.MEDIUM,
                "complexity_assessment": "Medium complexity - database compatibility issue",
                "estimated_effort": "2-4 days",
                "required_skills": ["PostgreSQL", "Database Migrations", "SQL", "Version Compatibility"],
                "action_plan": [
                    "Identify PostgreSQL 14 syntax changes",
                    "Update migration scripts",
                    "Test on PostgreSQL 14 environment",
                    "Add version compatibility checks",
                    "Update deployment documentation",
                    "Create rollback procedures"
                ],
                "risks": ["Data migration failures", "Downtime during migration", "Version-specific edge cases"]
            }
        }

        data = scope_data.get(issue_number, scope_data[123])  # Default to first issue

        return IssueScopeResult(
            issue_number=issue_number,
            confidence_score=data["confidence_score"],
            confidence_level=data["confidence_level"],
            complexity_assessment=data["complexity_assessment"],
            estimated_effort=data["estimated_effort"],
            required_skills=data["required_skills"],
            action_plan=data["action_plan"],
            risks=data["risks"],
            session_id=f"demo_session_{issue_number}",
            session_url=f"https://app.devin.ai/sessions/demo_{issue_number}"
        )

    @staticmethod
    def get_sample_completion_result(issue_number: int) -> TaskCompletionResult:
        """Generate sample completion result based on issue number"""
        completion_data = {
            123: {
                "status": "completed",
                "success": True,
                "completion_summary": "Successfully implemented OAuth2 authentication with GitHub and Google providers. Added login/logout functionality with session management.",
                "files_modified": [
                    "src/components/Login.jsx",
                    "src/components/AuthCallback.jsx",
                    "src/middleware/auth.js",
                    "src/utils/oauth.js",
                    "src/styles/auth.css",
                    "tests/auth.test.js"
                ],
                "pull_request_url": "https://github.com/example/repo/pull/456"
            },
            124: {
                "status": "completed",
                "success": True,
                "completion_summary": "Fixed memory leak in data processing pipeline by implementing streaming data processing and optimizing memory usage patterns.",
                "files_modified": [
                    "src/pipeline/processor.py",
                    "src/pipeline/memory_manager.py",
                    "src/utils/streaming.py",
                    "tests/test_memory_usage.py",
                    "monitoring/memory_alerts.py"
                ],
                "pull_request_url": "https://github.com/example/repo/pull/457"
            },
            125: {
                "status": "completed",
                "success": True,
                "completion_summary": "Updated API documentation with all current endpoints, added examples and improved formatting.",
                "files_modified": [
                    "docs/api/endpoints.md",
                    "docs/api/authentication.md",
                    "docs/api/examples.md",
                    "openapi.yaml"
                ],
                "pull_request_url": "https://github.com/example/repo/pull/458"
            },
            126: {
                "status": "completed",
                "success": True,
                "completion_summary": "Implemented dark mode toggle with theme persistence and updated all UI components for dark mode compatibility.",
                "files_modified": [
                    "src/components/ThemeToggle.jsx",
                    "src/styles/themes.css",
                    "src/utils/theme.js",
                    "src/components/Header.jsx",
                    "src/components/Sidebar.jsx",
                    "tests/theme.test.js"
                ],
                "pull_request_url": "https://github.com/example/repo/pull/459"
            },
            127: {
                "status": "completed",
                "success": True,
                "completion_summary": "Fixed PostgreSQL 14 compatibility issues in migration scripts and added version checks.",
                "files_modified": [
                    "migrations/001_initial.sql",
                    "migrations/002_user_tables.sql",
                    "scripts/migrate.py",
                    "scripts/version_check.py",
                    "docs/deployment.md"
                ],
                "pull_request_url": "https://github.com/example/repo/pull/460"
            }
        }

        data = completion_data.get(issue_number, completion_data[123])  # Default to first issue

        return TaskCompletionResult(
            issue_number=issue_number,
            status=data["status"],
            completion_summary=data["completion_summary"],
            files_modified=data["files_modified"],
            pull_request_url=data["pull_request_url"],
            session_id=f"demo_completion_{issue_number}",
            session_url=f"https://app.devin.ai/sessions/demo_completion_{issue_number}",
            success=data["success"],
            confidence_score=data.get("confidence_score", 0.85),
            confidence_level=ConfidenceLevel.HIGH,
            complexity_assessment=data.get("complexity_assessment", "Medium complexity implementation"),
            implementation_quality=data.get("implementation_quality", "High quality with proper error handling"),
            required_skills=data.get("required_skills", ["React/Frontend", "OAuth2", "Authentication"]),
            action_plan=data.get("action_plan", ["Implemented OAuth2 integration", "Added login components", "Created tests"]),
            risks=data.get("risks", ["OAuth provider changes", "Session security"]),
            test_coverage=data.get("test_coverage", "Comprehensive unit and integration tests")
        )

class DemoApp:
    """Demo application showing GitHub Issues Integration functionality"""

    def __init__(self):
        self.issues = DemoData.get_sample_issues()

    def display_issues(self):
        """Display issues in a formatted table"""
        table = Table(title="GitHub Issues - Demo Repository")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("State", style="green")
        table.add_column("Labels", style="blue")
        table.add_column("Assignees", style="yellow")

        for issue in self.issues:
            table.add_row(
                str(issue.number),
                issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                issue.state.value,
                ", ".join(issue.labels[:3]) + ("..." if len(issue.labels) > 3 else ""),
                ", ".join(issue.assignees[:2]) + ("..." if len(issue.assignees) > 2 else "")
            )

        console.print(table)

    def display_scope_result(self, result: IssueScopeResult):
        """Display issue scoping results"""
        confidence_color = "green" if result.confidence_level.value == "high" else "yellow" if result.confidence_level.value == "medium" else "red"

        panel_content = f"""
[bold]Confidence Score:[/bold] [{confidence_color}]{result.confidence_score:.2f} ({result.confidence_level.value})[/{confidence_color}]
[bold]Complexity:[/bold] {result.complexity_assessment}
[bold]Estimated Effort:[/bold] {result.estimated_effort}

[bold]Required Skills:[/bold]
{chr(10).join(f"• {skill}" for skill in result.required_skills)}

[bold]Action Plan:[/bold]
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(result.action_plan))}

[bold]Risks:[/bold]
{chr(10).join(f"• {risk}" for risk in result.risks)}

[bold]Devin Session:[/bold] {result.session_url}
"""

        panel = Panel(
            panel_content,
            title=f"Issue #{result.issue_number} Scope Analysis",
            border_style=confidence_color
        )
        console.print(panel)

    def display_completion_result(self, result: TaskCompletionResult):
        """Display task completion results"""
        status_color = "green" if result.success else "red"

        panel_content = f"""
[bold]Status:[/bold] [{status_color}]{result.status}[/{status_color}]
[bold]Success:[/bold] [{status_color}]{result.success}[/{status_color}]

[bold]Summary:[/bold]
{result.completion_summary}

[bold]Files Modified:[/bold]
{chr(10).join(f"• {file}" for file in result.files_modified)}

[bold]Pull Request:[/bold] {result.pull_request_url or "None created"}

[bold]Devin Session:[/bold] {result.session_url}
"""

        panel = Panel(
            panel_content,
            title=f"Issue #{result.issue_number} Completion Result",
            border_style=status_color
        )
        console.print(panel)

    async def demo_workflow(self):
        """Demonstrate the complete workflow"""
        console.print("[bold blue]🚀 GitHub Issues Integration with Devin - Demo Mode[/bold blue]\n")

        console.print("[bold]Step 1: Listing GitHub Issues[/bold]")
        self.display_issues()

        console.print(f"\n[bold]Step 2: Scoping Issue #123[/bold]")
        console.print("Analyzing issue with Devin...")
        await asyncio.sleep(1)  # Simulate API call

        scope_result = DemoData.get_sample_scope_result(123)
        self.display_scope_result(scope_result)

        console.print(f"\n[bold]Step 3: Completing Issue #123[/bold]")
        console.print("Triggering Devin session to complete the issue...")
        await asyncio.sleep(2)  # Simulate longer API call

        completion_result = DemoData.get_sample_completion_result(123)
        self.display_completion_result(completion_result)

        console.print(f"\n[bold green]✅ Demo Complete![/bold green]")
        console.print(f"The GitHub Issues Integration successfully:")
        console.print(f"• Listed issues from the repository")
        console.print(f"• Analyzed issue #123 with {scope_result.confidence_score:.0%} confidence")
        console.print(f"• Completed the issue and created PR: {completion_result.pull_request_url}")

async def main():
    """Run the demo"""
    demo = DemoApp()
    await demo.demo_workflow()

if __name__ == "__main__":
    asyncio.run(main())
