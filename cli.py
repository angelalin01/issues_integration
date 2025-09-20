import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List
from github_client import GitHubClient
from devin_client import DevinClient
from models import GitHubIssue, IssueScopeResult, TaskCompletionResult

console = Console()

class CLI:
    def __init__(self):
        self.github_client = GitHubClient()
        self.devin_client = DevinClient()
    
    def display_issues(self, issues: List[GitHubIssue]):
        """Display issues in a formatted table"""
        table = Table(title="GitHub Issues")
        table.add_column("Number", style="cyan", no_wrap=True)
        table.add_column("Title", style="magenta")
        table.add_column("State", style="green")
        table.add_column("Labels", style="blue")
        table.add_column("Assignees", style="yellow")
        
        for issue in issues:
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

@click.group()
def cli():
    """GitHub Issues Integration with Devin"""
    pass

@cli.command()
@click.option('--repo', required=True, help='Repository name (owner/repo)')
@click.option('--state', default='open', help='Issue state (open/closed)')
@click.option('--limit', default=20, help='Maximum number of issues to display')
def list_issues(repo: str, state: str, limit: int):
    """List GitHub issues"""
    cli_instance = CLI()
    
    try:
        with console.status(f"Fetching issues from {repo}..."):
            issues = cli_instance.github_client.list_issues(repo, state, limit)
        
        if not issues:
            console.print(f"[yellow]No {state} issues found in {repo}[/yellow]")
            return
        
        cli_instance.display_issues(issues)
        console.print(f"\n[green]Found {len(issues)} {state} issues in {repo}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
@click.option('--repo', required=True, help='Repository name (owner/repo)')
@click.option('--issue-number', required=True, type=int, help='Issue number to scope')
def scope_issue(repo: str, issue_number: int):
    """Scope an issue using Devin"""
    cli_instance = CLI()
    
    async def run_scope():
        try:
            with console.status(f"Fetching issue #{issue_number} from {repo}..."):
                issue = cli_instance.github_client.get_issue(repo, issue_number)
            
            console.print(f"[blue]Scoping issue: {issue.title}[/blue]")
            
            with console.status("Analyzing issue with Devin..."):
                scope_result = await cli_instance.devin_client.scope_issue(issue)
            
            cli_instance.display_scope_result(scope_result)
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run_scope())

@cli.command()
@click.option('--repo', required=True, help='Repository name (owner/repo)')
@click.option('--issue-number', required=True, type=int, help='Issue number to complete')
@click.option('--scope-first', is_flag=True, help='Scope the issue first before completing')
def complete_issue(repo: str, issue_number: int, scope_first: bool):
    """Complete an issue using Devin"""
    cli_instance = CLI()
    
    async def run_completion():
        try:
            with console.status(f"Fetching issue #{issue_number} from {repo}..."):
                issue = cli_instance.github_client.get_issue(repo, issue_number)
            
            console.print(f"[blue]Completing issue: {issue.title}[/blue]")
            
            scope_result = None
            if scope_first:
                with console.status("Scoping issue with Devin..."):
                    scope_result = await cli_instance.devin_client.scope_issue(issue)
                cli_instance.display_scope_result(scope_result)
                
                if not click.confirm(f"Proceed with completion? (Confidence: {scope_result.confidence_score:.2f})"):
                    console.print("[yellow]Completion cancelled[/yellow]")
                    return
            
            with console.status("Completing issue with Devin..."):
                completion_result = await cli_instance.devin_client.complete_issue(issue, scope_result)
            
            cli_instance.display_completion_result(completion_result)
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(run_completion())

@cli.command()
@click.option('--repo', required=True, help='Repository name (owner/repo)')
def dashboard(repo: str):
    """Interactive dashboard for managing issues"""
    cli_instance = CLI()
    
    try:
        with console.status(f"Loading issues from {repo}..."):
            issues = cli_instance.github_client.list_issues(repo, "open", 50)
        
        if not issues:
            console.print(f"[yellow]No open issues found in {repo}[/yellow]")
            return
        
        while True:
            console.clear()
            console.print(f"[bold blue]GitHub Issues Dashboard - {repo}[/bold blue]\n")
            
            cli_instance.display_issues(issues)
            
            console.print("\n[bold]Actions:[/bold]")
            console.print("1. Scope an issue")
            console.print("2. Complete an issue")
            console.print("3. Refresh issues")
            console.print("4. Exit")
            
            choice = click.prompt("\nSelect an action", type=int)
            
            if choice == 1:
                issue_num = click.prompt("Enter issue number to scope", type=int)
                issue = next((i for i in issues if i.number == issue_num), None)
                if issue:
                    async def scope():
                        scope_result = await cli_instance.devin_client.scope_issue(issue)
                        cli_instance.display_scope_result(scope_result)
                        click.pause()
                    asyncio.run(scope())
                else:
                    console.print(f"[red]Issue #{issue_num} not found[/red]")
                    click.pause()
            
            elif choice == 2:
                issue_num = click.prompt("Enter issue number to complete", type=int)
                issue = next((i for i in issues if i.number == issue_num), None)
                if issue:
                    async def complete():
                        completion_result = await cli_instance.devin_client.complete_issue(issue)
                        cli_instance.display_completion_result(completion_result)
                        click.pause()
                    asyncio.run(complete())
                else:
                    console.print(f"[red]Issue #{issue_num} not found[/red]")
                    click.pause()
            
            elif choice == 3:
                with console.status(f"Refreshing issues from {repo}..."):
                    issues = cli_instance.github_client.list_issues(repo, "open", 50)
            
            elif choice == 4:
                break
            
            else:
                console.print("[red]Invalid choice[/red]")
                click.pause()
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == '__main__':
    cli()
