from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class IssueState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

class GitHubIssue(BaseModel):
    number: int
    title: str
    body: Optional[str]
    state: IssueState
    created_at: datetime
    updated_at: datetime
    labels: List[str]
    assignees: List[str]
    url: str
    repository: str

class IssueScopeResult(BaseModel):
    issue_number: int
    confidence_score: float
    confidence_level: ConfidenceLevel
    complexity_assessment: str
    estimated_effort: str
    required_skills: List[str]
    action_plan: List[str]
    risks: List[str]
    session_id: str
    session_url: str

class TaskCompletionResult(BaseModel):
    issue_number: int
    status: str
    completion_summary: str
    files_modified: List[str]
    pull_request_url: Optional[str]
    session_id: str
    session_url: str
    success: bool
    confidence_score: float
    confidence_level: ConfidenceLevel
    complexity_assessment: str
    implementation_quality: str
    required_skills: List[str]
    action_plan: List[str]
    risks: List[str]
    test_coverage: str

class DevinSession(BaseModel):
    session_id: str
    url: str
    status: str
    created_at: datetime
    structured_output: Optional[Dict[str, Any]] = None
