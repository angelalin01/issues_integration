#!/usr/bin/env python3

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import subprocess
import sys
import os

console = Console()

def run_cli_demo(github_token: str = None, devin_api_key: str = None, repo_name: str = None):
    """Run CLI demo with provided credentials"""
    env = os.environ.copy()
    if github_token:
        env['GITHUB_TOKEN'] = github_token
    if devin_api_key:
        env['DEVIN_API_KEY'] = devin_api_key
    
    console.print(f"\n[bold blue]🚀 Running CLI Demo for {repo_name}[/bold blue]")
    
    commands = [
        f"python main.py list-issues --repo {repo_name} --limit 5",
        f"python main.py scope-issue --repo {repo_name} --issue-number 123",
        f"python main.py complete-issue --repo {repo_name} --issue-number 123"
    ]
    
    for cmd in commands:
        console.print(f"\n[dim]$ {cmd}[/dim]")
        try:
            result = subprocess.run(cmd.split(), env=env, capture_output=True, text=True)
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
        except Exception as e:
            console.print(f"[red]Error running command: {e}[/red]")

def run_web_demo(github_token: str = None, devin_api_key: str = None, repo_name: str = None):
    """Run web demo server"""
    console.print(f"\n[bold blue]🌐 Starting Web Demo Server[/bold blue]")
    
    env = os.environ.copy()
    if github_token:
        env['GITHUB_TOKEN'] = github_token
    if devin_api_key:
        env['DEVIN_API_KEY'] = devin_api_key
    
    console.print(f"[green]Repository: {repo_name}[/green]")
    console.print(f"[green]Mode: {'Live API' if github_token else 'Demo Mode'}[/green]")
    console.print(f"\n[yellow]Starting server... Open http://127.0.0.1:5000 in your browser[/yellow]")
    
    try:
        subprocess.run([sys.executable, "web_server.py"], env=env)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")

@click.command()
def main():
    """Interactive GitHub Issues Integration Demo"""
    
    console.print(Panel.fit(
        "[bold blue]🚀 GitHub Issues Integration with Devin[/bold blue]\n"
        "Interactive Demo Configuration",
        border_style="blue"
    ))
    
    console.print("\n[bold]Step 1: Choose Demo Type[/bold]")
    demo_type = Prompt.ask(
        "Select demo interface",
        choices=["cli", "web"],
        default="web"
    )
    
    console.print("\n[bold]Step 2: Configure API Access[/bold]")
    console.print("[dim]Leave empty to use demo mode with sample data[/dim]")
    
    github_token = Prompt.ask(
        "GitHub Token (optional)",
        password=True,
        default=""
    ).strip()
    
    devin_api_key = Prompt.ask(
        "Devin API Key (optional)",
        password=True,
        default=""
    ).strip()
    
    console.print("\n[bold]Step 3: Choose Repository[/bold]")
    repo_name = Prompt.ask(
        "GitHub Repository (owner/repo)",
        default="octocat/Hello-World"
    ).strip()
    
    if not repo_name:
        console.print("[red]Repository name is required[/red]")
        return
    
    mode = "Live API" if (github_token and devin_api_key) else "Demo Mode"
    console.print(f"\n[bold]Configuration Summary:[/bold]")
    console.print(f"Demo Type: [green]{demo_type.upper()}[/green]")
    console.print(f"Repository: [green]{repo_name}[/green]")
    console.print(f"Mode: [green]{mode}[/green]")
    
    if not Confirm.ask("\nProceed with demo?", default=True):
        console.print("[yellow]Demo cancelled[/yellow]")
        return
    
    if demo_type == "cli":
        run_cli_demo(github_token or None, devin_api_key or None, repo_name)
    else:
        run_web_demo(github_token or None, devin_api_key or None, repo_name)

if __name__ == '__main__':
    main()
