#!/usr/bin/env python3

"""
Simplified demo for GitHub Issues Integration with Devin
Works with basic Python 3.x without heavy dependencies
"""

import json
from datetime import datetime

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_table(headers, rows):
    """Print a simple table"""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_row)
    print("-" * len(header_row))
    
    for row in rows:
        row_str = " | ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        print(row_str)

def get_sample_issues():
    """Get sample GitHub issues"""
    return [
        {
            "number": 123,
            "title": "Add user authentication to login page",
            "state": "open",
            "labels": ["enhancement", "authentication", "frontend"],
            "assignees": ["developer1"]
        },
        {
            "number": 124,
            "title": "Fix memory leak in data processing pipeline",
            "state": "open", 
            "labels": ["bug", "performance", "backend"],
            "assignees": ["developer2"]
        },
        {
            "number": 125,
            "title": "Update documentation for API endpoints",
            "state": "open",
            "labels": ["documentation"],
            "assignees": []
        },
        {
            "number": 126,
            "title": "Implement dark mode toggle",
            "state": "open",
            "labels": ["enhancement", "ui", "frontend"],
            "assignees": ["designer1"]
        },
        {
            "number": 127,
            "title": "Database migration script fails on PostgreSQL 14",
            "state": "open",
            "labels": ["bug", "database", "migration"],
            "assignees": ["dba1"]
        }
    ]

def get_scope_result(issue_number):
    """Get sample scoping result"""
    return {
        "issue_number": issue_number,
        "confidence_score": 0.85,
        "confidence_level": "high",
        "complexity": "Medium complexity - requires OAuth integration and frontend changes",
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
        "risks": ["OAuth provider rate limits", "Session management complexity", "Security vulnerabilities"],
        "session_url": f"https://app.devin.ai/sessions/demo_{issue_number}"
    }

def get_completion_result(issue_number):
    """Get sample completion result"""
    return {
        "issue_number": issue_number,
        "status": "completed",
        "success": True,
        "summary": "Successfully implemented OAuth2 authentication with GitHub and Google providers. Added login/logout functionality with session management.",
        "files_modified": [
            "src/components/Login.jsx",
            "src/components/AuthCallback.jsx",
            "src/middleware/auth.js", 
            "src/utils/oauth.js",
            "src/styles/auth.css",
            "tests/auth.test.js"
        ],
        "pull_request_url": "https://github.com/example/repo/pull/456",
        "session_url": f"https://app.devin.ai/sessions/demo_completion_{issue_number}"
    }

def display_issues():
    """Display GitHub issues"""
    print_header("GitHub Issues - Demo Repository")
    
    issues = get_sample_issues()
    headers = ["Number", "Title", "State", "Labels", "Assignees"]
    rows = []
    
    for issue in issues:
        title = issue["title"][:40] + "..." if len(issue["title"]) > 40 else issue["title"]
        labels = ", ".join(issue["labels"][:2]) + ("..." if len(issue["labels"]) > 2 else "")
        assignees = ", ".join(issue["assignees"][:2]) + ("..." if len(issue["assignees"]) > 2 else "")
        
        rows.append([
            str(issue["number"]),
            title,
            issue["state"],
            labels,
            assignees
        ])
    
    print_table(headers, rows)

def display_scope_analysis(issue_number):
    """Display issue scoping analysis"""
    print_header(f"Issue #{issue_number} Scope Analysis")
    
    result = get_scope_result(issue_number)
    
    print(f"Confidence Score: {result['confidence_score']:.2f} ({result['confidence_level']})")
    print(f"Complexity: {result['complexity']}")
    print(f"Estimated Effort: {result['estimated_effort']}")
    print()
    
    print("Required Skills:")
    for skill in result['required_skills']:
        print(f"  • {skill}")
    print()
    
    print("Action Plan:")
    for i, step in enumerate(result['action_plan'], 1):
        print(f"  {i}. {step}")
    print()
    
    print("Risks:")
    for risk in result['risks']:
        print(f"  • {risk}")
    print()
    
    print(f"Devin Session: {result['session_url']}")

def display_completion_result(issue_number):
    """Display task completion result"""
    print_header(f"Issue #{issue_number} Completion Result")
    
    result = get_completion_result(issue_number)
    
    print(f"Status: {result['status']}")
    print(f"Success: {result['success']}")
    print()
    
    print("Summary:")
    print(f"  {result['summary']}")
    print()
    
    print("Files Modified:")
    for file in result['files_modified']:
        print(f"  • {file}")
    print()
    
    print(f"Pull Request: {result['pull_request_url']}")
    print(f"Devin Session: {result['session_url']}")

def main():
    """Run the simplified demo"""
    print("🚀 GitHub Issues Integration with Devin - Simple Demo Mode")
    print("(Compatible with basic Python 3.x)")
    
    print("\nStep 1: Listing GitHub Issues")
    display_issues()
    
    print("\nStep 2: Scoping Issue #123")
    print("Analyzing issue with Devin...")
    display_scope_analysis(123)
    
    print("\nStep 3: Completing Issue #123")
    print("Triggering Devin session to complete the issue...")
    display_completion_result(123)
    
    print_header("Demo Complete!")
    print("The GitHub Issues Integration successfully:")
    print("• Listed issues from the repository")
    print("• Analyzed issue #123 with 85% confidence")
    print("• Completed the issue and created PR: https://github.com/example/repo/pull/456")
    print()
    print("To use the full CLI with rich formatting, install Python 3.8+ and run:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  python demo.py")

if __name__ == "__main__":
    main()
