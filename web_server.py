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

def set_runtime_config(github_token=None, devin_api_key=None, repo_name=None, enable_commenting: bool = False):
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

    from config import Config as _Cfg
    original_key_env = os.environ.get('DEVIN_API_KEY')
    original_key_cfg = getattr(_Cfg, 'DEVIN_API_KEY', None)

    os.environ['DEVIN_API_KEY'] = runtime_config['devin_api_key']
    _Cfg.DEVIN_API_KEY = runtime_config['devin_api_key']

    try:
        print(f"[get_devin_client] Using Devin key prefix: {str(runtime_config['devin_api_key'])[:6]}")
        try:
            return DevinClient()
        except Exception as e:
            print(f"[get_devin_client] DevinClient init error: {e}")
            raise
    finally:
        if original_key_env is not None:
            os.environ['DEVIN_API_KEY'] = original_key_env
        elif 'DEVIN_API_KEY' in os.environ:
            del os.environ['DEVIN_API_KEY']
        _Cfg.DEVIN_API_KEY = original_key_cfg

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
@app.route('/api/test-devin-auth')
def test_devin_auth():
    try:
        if runtime_config['demo_mode'] or not runtime_config['devin_api_key']:
            return jsonify({'success': False, 'error': 'Configure a Devin API key first (not in demo mode).'})
        devin_client = get_devin_client()
        if not devin_client:
            return jsonify({'success': False, 'error': 'Devin client unavailable'})
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session = loop.run_until_complete(devin_client.create_session("Auth test: please just acknowledge."))
            return jsonify({'success': True, 'session_id': session.session_id, 'session_url': session.url})
        finally:
            loop.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
            # PROTECTION: Never return demo data in live mode
            if not runtime_config.get('demo_mode', False):
                # Verify this isn't demo data by checking for demo indicators
                if (isinstance(cached_result, dict) and 
                   (cached_result.get('session_id', '').startswith('demo-') or
                    cached_result.get('complexity_assessment') == 'Medium complexity - requires understanding of existing codebase')):
                    # This is demo data, don't return it in live mode
                    pass
                else:
                    if runtime_config['enable_commenting']:
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
            elif runtime_config.get('demo_mode', False):
                if runtime_config['enable_commenting']:
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
            prompt = f"""Please analyze this GitHub issue and provide a structured assessment:

Repository: {issue.repository}
Issue #{issue.number}: {issue.title}

Description:
{issue.body}

Labels: {', '.join(issue.labels)}
State: {issue.state}
URL: {issue.url}

Please provide a structured analysis with:
1. confidence_score (0.0 to 1.0) - how confident you are this can be completed successfully
2. confidence_level (low/medium/high) 
3. complexity_assessment - brief description of complexity
4. estimated_effort - time estimate (e.g., "2-4 hours", "1-2 days")
5. required_skills - list of technical skills needed
6. action_plan - step-by-step plan to complete the issue
7. risks - potential risks or blockers

Format your response as JSON with these exact field names."""
            
            session = loop.run_until_complete(devin_client.create_session(prompt))
            
            import threading
            thread = threading.Thread(
                target=lambda: asyncio.run(complete_scope_session(issue_number, session.session_id, issue))
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'demo_mode': False,
                'session_id': session.session_id,
                'session_url': session.url,
                'status': 'started'
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scope/<int:issue_number>/status/<session_id>')
def get_scope_status(issue_number, session_id):
    """Get the status of a scoping session"""
    try:
        if runtime_config['demo_mode']:
            import time
            import random
            
            stages = [
                {"status": "running", "progress": "Analyzing issue description..."},
                {"status": "running", "progress": "Evaluating complexity and requirements..."},
                {"status": "running", "progress": "Generating action plan..."},
                {"status": "completed", "progress": "Analysis complete"}
            ]
            
            stage_index = min(len(stages) - 1, abs(hash(session_id)) % len(stages))
            current_stage = stages[stage_index]
            
            if current_stage["status"] == "completed":
                cached_result = load_cached_result(issue_number, 'scope')
                if cached_result:
                    return jsonify({
                        'success': True,
                        'status': 'completed',
                        'result': cached_result
                    })
            
            return jsonify({
                'success': True,
                'status': current_stage["status"],
                'session_url': None,
                'progress_message': current_stage["progress"],
                'action_plan_preview': []
            })
        
        devin_client = get_devin_client()
        if not devin_client:
            return jsonify({'success': False, 'error': 'Devin client not available'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session = loop.run_until_complete(devin_client.get_session_status(session_id))
            print(f"DEBUG: Status endpoint - session {session_id} has status: {session.status}")
            
            if session.status in ["completed", "stopped", "blocked", "suspended"]:
                cached_result = load_cached_result(issue_number, 'scope')
                print(f"DEBUG: Looking for cached result for issue {issue_number}, found: {cached_result is not None}")
                if cached_result:
                    # PROTECTION: Never return demo data in live mode
                    if not runtime_config.get('demo_mode', False):
                        # Verify this isn't demo data by checking for demo indicators
                        if not (isinstance(cached_result, dict) and 
                               (cached_result.get('session_id', '').startswith('demo-') or
                                cached_result.get('complexity_assessment') == 'Medium complexity - requires understanding of existing codebase')):
                            return jsonify({
                                'success': True,
                                'status': session.status,
                                'session_url': cached_result.get('session_url') or getattr(session, 'url', None),
                                'result': cached_result
                            })
                    elif runtime_config.get('demo_mode', False):
                        return jsonify({
                            'success': True,
                            'status': session.status,
                            'session_url': cached_result.get('session_url'),
                            'result': cached_result
                        })
                
                # Return session structured output directly
                return jsonify({
                    'success': True,
                    'status': session.status,
                    'session_url': getattr(session, 'url', None),
                    'result': session.structured_output
                })
            else:
                progress_message = "Processing with Devin AI..."
                action_plan_preview = []
                if session.structured_output:
                    if isinstance(session.structured_output, dict):
                        progress_message = session.structured_output.get('progress', progress_message)
                        action_plan_preview = (session.structured_output.get('action_plan') or session.structured_output.get('plan') or [])[:3]
                
                return jsonify({
                    'success': True,
                    'status': session.status,
                    'session_url': getattr(session, 'url', None),
                    'progress_message': progress_message,
                    'action_plan_preview': action_plan_preview
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
            prompt = f"""
Please complete this GitHub issue by implementing the necessary changes:

Repository: {issue.repository}
Issue #{issue.number}: {issue.title}

Description:
{issue.body}

Labels: {', '.join(issue.labels)}
URL: {issue.url}

Please provide a structured response with all the fields as specified in the DevinClient.complete_issue method.

Format your response as JSON with these exact field names."""
            
            session = loop.run_until_complete(devin_client.create_session(prompt))
            
            import threading
            thread = threading.Thread(
                target=lambda: asyncio.run(complete_completion_session(issue_number, session.session_id, issue))
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'demo_mode': False,
                'cached': False,
                'session_id': session.session_id,
                'session_url': session.url
            })
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

async def complete_scope_session(issue_number, session_id, issue):
    """Background task to complete scoping session and cache result"""
    try:
        print(f"DEBUG: Starting background task for issue {issue_number}, session {session_id}")
        devin_client = get_devin_client()
        if not devin_client:
            print(f"DEBUG: No devin client available for session {session_id}")
            return
        
        print(f"DEBUG: Waiting for completion of session {session_id}")
        completed_session = await devin_client.wait_for_completion(session_id)
        print(f"DEBUG: Session {session_id} completed with status: {completed_session.status}")
        
        output = completed_session.structured_output or {}
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except Exception:
                output = {}
        
        cs_raw = output.get("confidence_score") or output.get("confidence") or 0.5
        try:
            confidence_score = float(cs_raw)
        except Exception:
            confidence_score = 0.5
        
        from models import ConfidenceLevel, IssueScopeResult
        if confidence_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        scope_result = IssueScopeResult(
            issue_number=issue.number,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            complexity_assessment=output.get("complexity_assessment") or output.get("complexity") or "Unknown complexity",
            estimated_effort=output.get("estimated_effort") or output.get("effort") or "Unknown effort",
            required_skills=output.get("required_skills") or output.get("skills") or [],
            action_plan=output.get("action_plan") or output.get("plan") or [],
            risks=output.get("risks") or [],
            session_id=session_id,
            session_url=completed_session.url or f"https://app.devin.ai/sessions/{session_id.replace('devin-', '')}"
        )
        
        result_dict = scope_result.dict()
        print(f"DEBUG: Saving cached result for issue {issue_number}: {result_dict}")
        save_cached_result(issue_number, 'scope', result_dict)
        print(f"DEBUG: Cached result saved successfully for issue {issue_number}")
        
        if runtime_config['enable_commenting']:
            github_client = get_github_client()
            if github_client:
                comment_body = format_scope_comment(result_dict, issue_number)
                comment_result = github_client.add_issue_comment(
                    runtime_config['repo_name'], issue_number, comment_body
                )
                result_dict['comment_posted'] = comment_result
                save_cached_result(issue_number, 'scope', result_dict)
                
    except Exception as e:
        print(f"DEBUG: Error completing scope session {session_id}: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")

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

@app.route('/api/complete/<int:issue_number>/status/<session_id>')
def get_completion_status(issue_number, session_id):
    """Get the status of a completion session"""
    try:
        if runtime_config['demo_mode']:
            import time
            import random
            
            stages = [
                {"status": "running", "progress": "Analyzing codebase...", "action_plan": ["Analyze repository structure", "Identify relevant files", "Understand codebase patterns"]},
                {"status": "running", "progress": "Implementing changes...", "action_plan": ["Create implementation plan", "Write code changes", "Update documentation"]},
                {"status": "running", "progress": "Creating tests...", "action_plan": ["Design test cases", "Write unit tests", "Verify test coverage"]},
                {"status": "running", "progress": "Creating pull request...", "action_plan": ["Commit changes", "Create PR description", "Submit pull request"]},
                {"status": "completed", "progress": "Implementation complete", "action_plan": []}
            ]
            
            stage_index = min(len(stages) - 1, abs(hash(session_id)) % len(stages))
            current_stage = stages[stage_index]
            
            if current_stage["status"] == "completed":
                cached_result = load_cached_result(issue_number, 'complete')
                if cached_result:
                    return jsonify({
                        'success': True,
                        'status': 'completed',
                        'session_url': cached_result.get('session_url'),
                        'result': cached_result
                    })
            
            return jsonify({
                'success': True,
                'status': current_stage["status"],
                'progress_message': current_stage["progress"],
                'action_plan_preview': current_stage["action_plan"]
            })
        
        devin_client = get_devin_client()
        if not devin_client:
            return jsonify({'success': False, 'error': 'Devin client not available'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session = loop.run_until_complete(devin_client.get_session_status(session_id))
            print(f"DEBUG: Completion status endpoint - session {session_id} has status: {session.status}")
            
            if session.status in ["completed", "stopped", "blocked", "suspended"]:
                cached_result = load_cached_result(issue_number, 'complete')
                print(f"DEBUG: Looking for cached completion result for issue {issue_number}, found: {cached_result is not None}")
                if cached_result:
                    # PROTECTION: Never return demo data in live mode
                    if not runtime_config.get('demo_mode', False):
                        # Verify this isn't demo data by checking for demo indicators
                        if not (isinstance(cached_result, dict) and 
                               (cached_result.get('session_id', '').startswith('demo-') or
                                cached_result.get('completion_summary') == 'Successfully implemented OAuth2 authentication with GitHub and Google providers. Added login/logout functionality with session management.')):
                            return jsonify({
                                'success': True,
                                'status': session.status,
                                'session_url': cached_result.get('session_url') or getattr(session, 'url', None),
                                'result': cached_result
                            })
                    elif runtime_config.get('demo_mode', False):
                        return jsonify({
                            'success': True,
                            'status': session.status,
                            'session_url': cached_result.get('session_url'),
                            'result': cached_result
                        })
                
                # Return session structured output directly
                return jsonify({
                    'success': True,
                    'status': session.status,
                    'session_url': getattr(session, 'url', None),
                    'result': session.structured_output
                })
            else:
                progress_message = "Processing with Devin AI..."
                action_plan_preview = []
                if session.structured_output:
                    if isinstance(session.structured_output, dict):
                        progress_message = session.structured_output.get('progress', progress_message)
                        action_plan_preview = (session.structured_output.get('action_plan') or session.structured_output.get('plan') or [])[:3]
                
                return jsonify({
                    'success': True,
                    'status': session.status,
                    'session_url': getattr(session, 'url', None),
                    'progress_message': progress_message,
                    'action_plan_preview': action_plan_preview
                })
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

async def complete_completion_session(issue_number, session_id, issue):
    """Background task to complete completion session and cache result"""
    try:
        print(f"DEBUG: Starting background completion task for issue {issue_number}, session {session_id}")
        devin_client = get_devin_client()
        if not devin_client:
            print(f"DEBUG: No devin client available for completion session {session_id}")
            return
        
        print(f"DEBUG: Waiting for completion of session {session_id}")
        completed_session = await devin_client.wait_for_completion(session_id)
        print(f"DEBUG: Completion session {session_id} completed with status: {completed_session.status}")
        
        output = completed_session.structured_output or {}
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except Exception:
                output = {}
        
        cs_raw = output.get("confidence_score") or output.get("confidence") or 0.5
        try:
            confidence_score = float(cs_raw)
        except Exception:
            confidence_score = 0.5
        
        from models import ConfidenceLevel, TaskCompletionResult
        if confidence_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        completion_result = TaskCompletionResult(
            issue_number=issue.number,
            status=output.get("status") or "unknown",
            completion_summary=output.get("completion_summary") or output.get("summary") or "No summary available",
            files_modified=output.get("files_modified") or output.get("files") or [],
            pull_request_url=output.get("pull_request_url"),
            session_id=session_id,
            session_url=completed_session.url or f"https://app.devin.ai/sessions/{session_id.replace('devin-', '')}",
            success=bool(output.get("success", False)),
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            complexity_assessment=output.get("complexity_assessment") or output.get("complexity") or "Unknown complexity",
            implementation_quality=output.get("implementation_quality") or "Unknown quality",
            required_skills=output.get("required_skills") or output.get("skills") or [],
            action_plan=output.get("action_plan") or output.get("plan") or [],
            risks=output.get("risks") or [],
            test_coverage=output.get("test_coverage") or "Unknown coverage"
        )
        
        result_dict = completion_result.dict()
        print(f"DEBUG: Saving cached completion result for issue {issue_number}: {result_dict}")
        save_cached_result(issue_number, 'complete', result_dict)
        print(f"DEBUG: Cached completion result saved successfully for issue {issue_number}")
        
        if runtime_config['enable_commenting']:
            github_client = get_github_client()
            if github_client:
                comment_body = format_completion_comment(result_dict, issue_number)
                comment_result = github_client.add_issue_comment(
                    runtime_config['repo_name'], issue_number, comment_body
                )
                result_dict['comment_posted'] = comment_result
                save_cached_result(issue_number, 'complete', result_dict)
                
    except Exception as e:
        print(f"DEBUG: Error completing completion session {session_id}: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")

def run_server(host='127.0.0.1', port=5000):
    """Run the Flask server"""
    print(f"🚀 Starting GitHub Issues Integration Web Server")
    print(f"📍 Server running at: http://{host}:{port}")
    print(f"🌐 Open your browser to view the interactive demo")
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_server()
