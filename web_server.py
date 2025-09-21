#!/usr/bin/env python3

import asyncio
import json
import glob
from typing import Optional, Dict, Any, List
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from github_client import GitHubClient
from devin_client import DevinClient
from demo import DemoData
from models import GitHubIssue
from config import Config
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

runtime_config = {
    'github_token': None,
    'devin_api_key': None,
    'repo_name': None,
    'demo_mode': True,
    'enable_commenting': False
}

def set_runtime_config(github_token: str = None, devin_api_key: str = None, repo_name: str = None, enable_commenting: bool = False):
    """Set runtime configuration for API calls"""
    global runtime_config
    runtime_config['github_token'] = github_token
    runtime_config['devin_api_key'] = devin_api_key
    runtime_config['repo_name'] = repo_name
    runtime_config['demo_mode'] = not (github_token and repo_name)
    runtime_config['enable_commenting'] = enable_commenting

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
            
            def add_issue_comment(self, repo_name: str, issue_number: int, comment_body: str):
                """Add a comment to a GitHub issue"""
                try:
                    repo = self.get_repository(repo_name)
                    issue = repo.get_issue(issue_number)
                    comment = issue.create_comment(comment_body)
                    return {
                        'success': True,
                        'comment_id': comment.id,
                        'comment_url': comment.html_url
                    }
                except Exception as e:
                    if "write" in str(e).lower() or "permission" in str(e).lower():
                        return {
                            'success': False,
                            'error': f"GitHub token does not have write permissions for {repo_name}. Please ensure your token has 'repo' scope."
                        }
                    return {
                        'success': False,
                        'error': f"Failed to add comment to issue #{issue_number}: {str(e)}"
                    }
            
            def delete_issue_comment(self, repo_name: str, comment_id: int):
                """Delete a GitHub issue comment"""
                try:
                    repo = self.get_repository(repo_name)
                    comment = repo.get_issue_comment(comment_id)
                    comment.delete()
                    return {'success': True}
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"Failed to delete comment {comment_id}: {str(e)}"
                    }
            
            def list_issue_comments(self, repo_name: str, issue_number: int):
                """List comments for a GitHub issue"""
                try:
                    repo = self.get_repository(repo_name)
                    issue = repo.get_issue(issue_number)
                    comments = issue.get_comments()
                    return [
                        {
                            'id': comment.id,
                            'body': comment.body,
                            'created_at': comment.created_at.isoformat(),
                            'user': comment.user.login,
                            'html_url': comment.html_url
                        }
                        for comment in comments
                    ]
                except Exception as e:
                    raise Exception(f"Failed to fetch comments for issue #{issue_number}: {str(e)}")
            
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

def load_cached_result(issue_number: int, result_type: str):
    """Load cached result from file"""
    cache_file = f"cache/issue_{issue_number}_{result_type}.json"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading cache file {cache_file}: {e}")
    return None

def save_cached_result(issue_number: int, result_type: str, result_data: dict):
    """Save result to cache file"""
    cache_file = f"cache/issue_{issue_number}_{result_type}.json"
    try:
        os.makedirs("cache", exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving cache file {cache_file}: {e}")

def format_scope_comment(scope_result: dict, issue_number: int) -> str:
    """Format scoping result as GitHub comment"""
    confidence = scope_result.get('confidence_score', 0)
    complexity = scope_result.get('complexity_assessment', 'Unknown')
    action_plan = scope_result.get('action_plan', [])
    session_url = scope_result.get('session_url', 'Not available')
    
    if isinstance(action_plan, list):
        action_plan_text = '\n'.join(f"{i+1}. {step}" for i, step in enumerate(action_plan))
    else:
        action_plan_text = str(action_plan)
    
    return f"""## 🤖 Devin Automation - Issue Scoping

**Confidence:** {confidence:.1f}/10
**Complexity:** {complexity}

**Action Plan:**
{action_plan_text}

**Devin Session:** {session_url}

---
*This comment was automatically generated by Devin Automation*"""

def format_completion_comment(completion_result: dict, issue_number: int) -> str:
    """Format completion result as GitHub comment"""
    status = completion_result.get('status', 'Unknown')
    summary = completion_result.get('completion_summary', 'No summary available')
    files_changed = completion_result.get('files_modified', [])
    pr_url = completion_result.get('pull_request_url', 'Not available')
    session_url = completion_result.get('session_url', 'Not available')
    
    files_text = '\n'.join(f"- {file}" for file in files_changed) if files_changed else "No files modified"
    
    return f"""## 🤖 Devin Automation - Task Completion

**Status:** {status}
**Summary:** {summary}

**Files Changed:**
{files_text}

**PR Link:** {pr_url}
**Devin Session:** {session_url}

---
*This comment was automatically generated by Devin Automation*"""

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
        repo_name=data.get('repo_name'),
        enable_commenting=data.get('enable_commenting', False)
    )
    return jsonify({
        'success': True,
        'demo_mode': runtime_config['demo_mode'],
        'repo_name': runtime_config['repo_name'],
        'enable_commenting': runtime_config['enable_commenting']
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
        cached_result = load_cached_result(issue_number, 'scope')
        if cached_result:
            if runtime_config['enable_commenting'] and not runtime_config['demo_mode']:
                github_client = get_github_client()
                if github_client:
                    comment_body = format_scope_comment(cached_result, issue_number)
                    comment_result = github_client.add_issue_comment(
                        runtime_config['repo_name'], issue_number, comment_body
                    )
                    cached_result['comment_posted'] = comment_result
            
            return jsonify({
                'success': True,
                'demo_mode': runtime_config['demo_mode'],
                'cached': True,
                'result': cached_result
            })
        
        if runtime_config['demo_mode']:
            # Demo mode - use canned responses, no commenting
            scope_result = DemoData.get_sample_scope_result(issue_number)
            result_dict = scope_result.dict()
            
            save_cached_result(issue_number, 'scope', result_dict)
            
            return jsonify({
                'success': True,
                'demo_mode': True,
                'cached': False,
                'result': result_dict
            })
        
        github_client = get_github_client()
        devin_client = get_devin_client()
        
        if not github_client:
            return jsonify({'success': False, 'error': 'GitHub token not configured or invalid'})
        
        if not devin_client:
            return jsonify({'success': False, 'error': 'Devin API key not available - scoping requires a valid Devin API key'})
        
        issue = github_client.get_issue(runtime_config['repo_name'], issue_number)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            scope_result = loop.run_until_complete(devin_client.scope_issue(issue))
            result_dict = scope_result.dict()
            
            save_cached_result(issue_number, 'scope', result_dict)
            
            if runtime_config['enable_commenting']:
                comment_body = format_scope_comment(result_dict, issue_number)
                comment_result = github_client.add_issue_comment(
                    runtime_config['repo_name'], issue_number, comment_body
                )
                result_dict['comment_posted'] = comment_result
            
            return jsonify({
                'success': True,
                'demo_mode': False,
                'cached': False,
                'result': result_dict
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete/<int:issue_number>')
def complete_issue(issue_number):
    """Complete an issue"""
    try:
        cached_result = load_cached_result(issue_number, 'complete')
        if cached_result:
            if runtime_config['enable_commenting'] and not runtime_config['demo_mode']:
                github_client = get_github_client()
                if github_client:
                    comment_body = format_completion_comment(cached_result, issue_number)
                    comment_result = github_client.add_issue_comment(
                        runtime_config['repo_name'], issue_number, comment_body
                    )
                    cached_result['comment_posted'] = comment_result
            
            return jsonify({
                'success': True,
                'demo_mode': runtime_config['demo_mode'],
                'cached': True,
                'result': cached_result
            })
        
        if runtime_config['demo_mode']:
            # Demo mode - use canned responses, no commenting
            completion_result = DemoData.get_sample_completion_result(issue_number)
            result_dict = completion_result.dict()
            
            save_cached_result(issue_number, 'complete', result_dict)
            
            return jsonify({
                'success': True,
                'demo_mode': True,
                'cached': False,
                'result': result_dict
            })
        
        github_client = get_github_client()
        devin_client = get_devin_client()
        
        if not github_client:
            return jsonify({'success': False, 'error': 'GitHub token not configured or invalid'})
        
        if not devin_client:
            return jsonify({'success': False, 'error': 'Devin API key not available - task completion requires a valid Devin API key'})
        
        issue = github_client.get_issue(runtime_config['repo_name'], issue_number)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            completion_result = loop.run_until_complete(devin_client.complete_issue(issue))
            result_dict = completion_result.dict()
            
            save_cached_result(issue_number, 'complete', result_dict)
            
            if runtime_config['enable_commenting']:
                comment_body = format_completion_comment(result_dict, issue_number)
                comment_result = github_client.add_issue_comment(
                    runtime_config['repo_name'], issue_number, comment_body
                )
                result_dict['comment_posted'] = comment_result
            
            return jsonify({
                'success': True,
                'demo_mode': False,
                'cached': False,
                'result': result_dict
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cleanup/comments', methods=['POST'])
def cleanup_comments():
    """Delete all Devin automation comments from issues"""
    try:
        data = request.json or {}
        issue_numbers = data.get('issue_numbers', [])
        
        if not issue_numbers:
            return jsonify({
                'success': False,
                'error': 'No issue numbers provided'
            })
        
        if runtime_config['demo_mode']:
            return jsonify({
                'success': True,
                'deleted_count': 0,
                'errors': [],
                'message': 'Demo mode - no actual comments to delete'
            })
        
        github_client = get_github_client()
        if not github_client:
            return jsonify({
                'success': False,
                'error': 'GitHub client not available'
            })
        
        deleted_count = 0
        errors = []
        
        for issue_number in issue_numbers:
            try:
                comments = github_client.list_issue_comments(runtime_config['repo_name'], issue_number)
                for comment in comments:
                    if comment['body'].startswith('## 🤖 Devin Automation'):
                        result = github_client.delete_issue_comment(runtime_config['repo_name'], comment['id'])
                        if result['success']:
                            deleted_count += 1
                        else:
                            errors.append(f"Issue #{issue_number}, Comment {comment['id']}: {result['error']}")
            except Exception as e:
                errors.append(f"Issue #{issue_number}: {str(e)}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cached results"""
    try:
        data = request.json or {}
        issue_numbers = data.get('issue_numbers', [])
        result_types = data.get('result_types', ['scope', 'complete'])
        
        cleared_files = []
        
        if issue_numbers:
            for issue_number in issue_numbers:
                for result_type in result_types:
                    cache_file = f"cache/issue_{issue_number}_{result_type}.json"
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                        cleared_files.append(cache_file)
        else:
            if os.path.exists("cache"):
                for filename in os.listdir("cache"):
                    if filename.endswith('.json'):
                        file_path = os.path.join("cache", filename)
                        os.remove(file_path)
                        cleared_files.append(file_path)
        
        return jsonify({
            'success': True,
            'cleared_files': cleared_files
        })
        
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
