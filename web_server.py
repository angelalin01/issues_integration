#!/usr/bin/env python3

import asyncio
import json
from typing import Optional
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from github_client import GitHubClient
from devin_client import DevinClient
from demo import DemoData
from models import GitHubIssue
from config import Config
import os

app = Flask(__name__)
CORS(app)

runtime_config = {
    'github_token': None,
    'devin_api_key': None,
    'repo_name': None,
    'demo_mode': True
}

def set_runtime_config(github_token: str = None, devin_api_key: str = None, repo_name: str = None):
    """Set runtime configuration for API calls"""
    global runtime_config
    runtime_config['github_token'] = github_token
    runtime_config['devin_api_key'] = devin_api_key
    runtime_config['repo_name'] = repo_name
    runtime_config['demo_mode'] = not (github_token and repo_name)

def get_github_client():
    """Get GitHub client with runtime config"""
    if runtime_config['demo_mode'] or not runtime_config['github_token']:
        return None
    
    original_token = os.environ.get('GITHUB_TOKEN')
    os.environ['GITHUB_TOKEN'] = runtime_config['github_token']
    
    try:
        from github import Github
        github = Github(runtime_config['github_token'])
        
        class RuntimeGitHubClient:
            def __init__(self):
                self.github = github
            
            def get_repository(self, repo_name: str):
                return self.github.get_repo(repo_name)
            
            def list_issues(self, repo_name: str, state: str = "open", limit: int = 50):
                from models import IssueState
                try:
                    repo = self.get_repository(repo_name)
                    issues = repo.get_issues(state=state)
                    
                    github_issues = []
                    count = 0
                    
                    for issue in issues:
                        if count >= limit:
                            break
                            
                        if issue.pull_request:
                            continue
                            
                        github_issue = GitHubIssue(
                            number=issue.number,
                            title=issue.title,
                            body=issue.body or "",
                            state=IssueState(issue.state),
                            created_at=issue.created_at,
                            updated_at=issue.updated_at,
                            labels=[label.name for label in issue.labels],
                            assignees=[assignee.login for assignee in issue.assignees],
                            url=issue.html_url,
                            repository=repo_name
                        )
                        github_issues.append(github_issue)
                        count += 1
                        
                    return github_issues
                    
                except Exception as e:
                    raise Exception(f"Failed to fetch issues from {repo_name}: {str(e)}")
            
            def get_issue(self, repo_name: str, issue_number: int):
                from models import IssueState
                try:
                    repo = self.get_repository(repo_name)
                    issue = repo.get_issue(issue_number)
                    
                    return GitHubIssue(
                        number=issue.number,
                        title=issue.title,
                        body=issue.body or "",
                        state=IssueState(issue.state),
                        created_at=issue.created_at,
                        updated_at=issue.updated_at,
                        labels=[label.name for label in issue.labels],
                        assignees=[assignee.login for assignee in issue.assignees],
                        url=issue.html_url,
                        repository=repo_name
                    )
                    
                except Exception as e:
                    raise Exception(f"Failed to fetch issue #{issue_number} from {repo_name}: {str(e)}")
        
        return RuntimeGitHubClient()
    finally:
        if original_token:
            os.environ['GITHUB_TOKEN'] = original_token
        elif 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']

def get_devin_client():
    """Get Devin client with runtime config"""
    if runtime_config['demo_mode'] or not runtime_config['devin_api_key']:
        return None
    
    original_key = os.environ.get('DEVIN_API_KEY')
    os.environ['DEVIN_API_KEY'] = runtime_config['devin_api_key']
    
    try:
        return DevinClient()
    finally:
        if original_key:
            os.environ['DEVIN_API_KEY'] = original_key
        elif 'DEVIN_API_KEY' in os.environ:
            del os.environ['DEVIN_API_KEY']

@app.route('/')
def index():
    """Serve the web demo interface"""
    with open('demo_web_interactive.html', 'r') as f:
        return f.read()

@app.route('/api/config', methods=['POST'])
def configure():
    """Configure API credentials and repo"""
    data = request.json
    set_runtime_config(
        github_token=data.get('github_token'),
        devin_api_key=data.get('devin_api_key'),
        repo_name=data.get('repo_name')
    )
    return jsonify({
        'success': True,
        'demo_mode': runtime_config['demo_mode'],
        'repo_name': runtime_config['repo_name']
    })

@app.route('/api/issues')
def list_issues():
    """List GitHub issues"""
    try:
        if runtime_config['demo_mode']:
            issues = DemoData.get_sample_issues()
            return jsonify({
                'success': True,
                'demo_mode': True,
                'issues': [issue.dict() for issue in issues]
            })
        
        github_client = get_github_client()
        if not github_client:
            return jsonify({'success': False, 'error': 'GitHub client not available'})
        
        issues = github_client.list_issues(runtime_config['repo_name'], 'open', 20)
        return jsonify({
            'success': True,
            'demo_mode': False,
            'issues': [issue.dict() for issue in issues]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scope/<int:issue_number>')
def scope_issue(issue_number):
    """Scope an issue"""
    try:
        if runtime_config['demo_mode']:
            scope_result = DemoData.get_sample_scope_result(issue_number)
            return jsonify({
                'success': True,
                'demo_mode': True,
                'result': scope_result.dict()
            })
        
        github_client = get_github_client()
        devin_client = get_devin_client()
        
        if not github_client or not devin_client:
            return jsonify({'success': False, 'error': 'API clients not available'})
        
        issue = github_client.get_issue(runtime_config['repo_name'], issue_number)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            scope_result = loop.run_until_complete(devin_client.scope_issue(issue))
            return jsonify({
                'success': True,
                'demo_mode': False,
                'result': scope_result.dict()
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete/<int:issue_number>')
def complete_issue(issue_number):
    """Complete an issue"""
    try:
        if runtime_config['demo_mode']:
            completion_result = DemoData.get_sample_completion_result(issue_number)
            return jsonify({
                'success': True,
                'demo_mode': True,
                'result': completion_result.dict()
            })
        
        github_client = get_github_client()
        devin_client = get_devin_client()
        
        if not github_client or not devin_client:
            return jsonify({'success': False, 'error': 'API clients not available'})
        
        issue = github_client.get_issue(runtime_config['repo_name'], issue_number)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            completion_result = loop.run_until_complete(devin_client.complete_issue(issue))
            return jsonify({
                'success': True,
                'demo_mode': False,
                'result': completion_result.dict()
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def run_server(host='127.0.0.1', port=5000):
    """Run the Flask server"""
    print(f"🚀 Starting GitHub Issues Integration Web Server")
    print(f"📍 Server running at: http://{host}:{port}")
    print(f"🌐 Open your browser to view the interactive demo")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_server()
