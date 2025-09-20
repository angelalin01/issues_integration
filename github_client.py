import asyncio
from typing import List, Optional
from github import Github
from github.Issue import Issue
from models import GitHubIssue, IssueState
from config import Config

class GitHubClient:
    def __init__(self):
        Config.validate()
        self.github = Github(Config.GITHUB_TOKEN)
    
    def get_repository(self, repo_name: str):
        """Get repository object"""
        return self.github.get_repo(repo_name)
    
    def list_issues(self, repo_name: str, state: str = "open", limit: int = 50) -> List[GitHubIssue]:
        """List issues from a GitHub repository"""
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
    
    def get_issue(self, repo_name: str, issue_number: int) -> GitHubIssue:
        """Get a specific issue"""
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
