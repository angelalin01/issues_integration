import re
from typing import Optional
from datetime import datetime

def validate_repo_name(repo_name: str) -> bool:
    """Validate GitHub repository name format (owner/repo)"""
    pattern = r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'
    return bool(re.match(pattern, repo_name))

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_issue_url(url: str) -> Optional[tuple[str, int]]:
    """Parse GitHub issue URL to extract repo and issue number"""
    pattern = r'https://github\.com/([^/]+/[^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if match:
        repo_name = match.group(1)
        issue_number = int(match.group(2))
        return repo_name, issue_number
    return None

def calculate_confidence_level(score: float) -> str:
    """Calculate confidence level from numerical score"""
    if score >= 0.8:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"

def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")
