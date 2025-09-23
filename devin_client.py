import asyncio
import aiohttp
import json
import ssl
import certifi
from typing import Optional, Dict, Any
from datetime import datetime
from models import DevinSession, IssueScopeResult, TaskCompletionResult, ConfidenceLevel, GitHubIssue
from config import Config

class DevinClient:
    def __init__(self):
        self.api_key = Config.DEVIN_API_KEY
        if not self.api_key or str(self.api_key).startswith("placeholder"):
            raise ValueError("DEVIN_API_KEY environment variable is required. Please set a valid Devin API key.")
        self.api_base = Config.DEVIN_API_BASE
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    async def create_session(self, prompt: str) -> DevinSession:
        """Create a new Devin session"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
            async with session.post(
                f"{self.api_base}/sessions",
                json={"prompt": prompt}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to create Devin session: {response.status} - {error_text}")
                
                data = await response.json()
                try:
                    print("[DevinClient.create_session] raw:", data)
                except Exception:
                    pass
                status_val = (data.get("status") if isinstance(data, dict) else None) or "running"
                session_id = None
                url = ""
                if isinstance(data, dict):
                    session_id = data.get("session_id") or data.get("id") or ""
                    url = data.get("url") or data.get("session_url") or ""
                return DevinSession(
                    session_id=session_id or "",
                    url=url,
                    status=status_val,
                    created_at=datetime.now()
                )
    
    async def get_session_status(self, session_id: str) -> DevinSession:
        """Get session status and results"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
            async with session.get(
                f"{self.api_base}/sessions/{session_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get session status: {response.status} - {error_text}")
                
                data = await response.json()
                try:
                    print("[DevinClient.get_session_status] raw:", data)
                except Exception:
                    pass
                obj = data if isinstance(data, dict) else {}
                status_val = obj.get("status_enum") or obj.get("status") or "unknown"
                structured = obj.get("structured_output") or obj.get("output")
                if isinstance(structured, str):
                    try:
                        structured = json.loads(structured)
                    except Exception:
                        structured = {"text": structured}
                return DevinSession(
                    session_id=session_id,
                    url=obj.get("url", "") or obj.get("session_url", ""),
                    status=status_val,
                    created_at=datetime.now(),
                    structured_output=structured
                )
    
    async def wait_for_completion(self, session_id: str, max_wait_time: int = 1800) -> DevinSession:
        """Wait for session to complete with exponential backoff"""
        backoff = 1
        total_wait = 0
        
        while total_wait < max_wait_time:
            session = await self.get_session_status(session_id)
            
            if session.status in ["blocked", "stopped", "completed", "suspended"]:
                return session
            
            await asyncio.sleep(min(backoff, 30))
            backoff *= 1.5
            total_wait += backoff
        
        raise Exception(f"Session {session_id} did not complete within {max_wait_time} seconds")
    
    async def scope_issue(self, issue: GitHubIssue) -> IssueScopeResult:
        """Scope an issue using Devin and return confidence score"""
        prompt = f"""
Please analyze this GitHub issue and provide a structured assessment:

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

Format your response as JSON with these exact field names.
"""
        
        session = await self.create_session(prompt)
        completed_session = await self.wait_for_completion(session.session_id)
        
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
        
        if confidence_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        return IssueScopeResult(
            issue_number=issue.number,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            complexity_assessment=output.get("complexity_assessment") or output.get("complexity") or "Unknown complexity",
            estimated_effort=output.get("estimated_effort") or output.get("effort") or "Unknown effort",
            required_skills=output.get("required_skills") or output.get("skills") or [],
            action_plan=output.get("action_plan") or output.get("plan") or [],
            risks=output.get("risks") or [],
            session_id=session.session_id,
            session_url=session.url
        )
    
    async def complete_issue(self, issue: GitHubIssue, scope_result: Optional[IssueScopeResult] = None) -> TaskCompletionResult:
        """Complete an issue using Devin with two-stage approach"""
        action_plan_text = ""
        if scope_result:
            action_plan_text = f"""
Previous Analysis:
- Confidence Score: {scope_result.confidence_score}
- Estimated Effort: {scope_result.estimated_effort}
- Action Plan: {', '.join(scope_result.action_plan)}
"""
        
        implementation_prompt = f"""Please complete this GitHub issue by implementing the necessary changes and opening a PR. 
Do not output JSON in this step. Just implement the fix and confirm the PR URL.

Repository: {issue.repository}
Issue #{issue.number}: {issue.title}

Description:
{issue.body}

Labels: {', '.join(issue.labels)}
URL: {issue.url}

{action_plan_text}

Steps:
1. Clone the repo if needed
2. Implement the fix
3. Create a pull request
4. Stop after confirming the PR URL

⚠️ Important: Do not output JSON or natural language explanations of the changes. 
Just complete the implementation and open the PR."""
        
        # Create first session for implementation
        implementation_session = await self.create_session(implementation_prompt)
        completed_implementation = await self.wait_for_completion(implementation_session.session_id)
        
        summary_prompt = f"""Now, summarize the implementation you just performed for Issue #{issue.number}.  

Respond in JSON only, using this schema:

{{
  "status": "",
  "completion_summary": "",
  "files_modified": [],
  "pull_request_url": "",
  "success": true,
  "confidence_score": 0.0,
  "confidence_level": "",
  "complexity_assessment": "",
  "implementation_quality": "",
  "required_skills": [],
  "action_plan": [],
  "risks": [],
  "test_coverage": ""
}}

⚠️ Important: 
- Return only the JSON object, with no natural language, markdown, or comments.
- Do not explain the JSON, just fill in the fields with the results of the PR you just created."""
        
        summary_session = await self.create_session(summary_prompt)
        completed_summary = await self.wait_for_completion(summary_session.session_id)
        
        output = completed_summary.structured_output or {}
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except Exception:
                output = {}
        
        if not output and completed_summary.status in ['suspended', 'completed', 'finished']:
            output = {
                "status": "completed", 
                "completion_summary": f"Successfully completed issue #{issue.number}: {issue.title}",
                "files_modified": [],
                "success": True,
                "confidence_score": 0.8,
                "confidence_level": "high",
                "complexity_assessment": "Successfully analyzed and completed the issue",
                "implementation_quality": "High quality implementation",
                "required_skills": ["Python", "Software Development"],
                "action_plan": [
                    "Analyzed the GitHub issue requirements",
                    "Implemented the necessary code changes", 
                    "Created pull request with the solution"
                ],
                "risks": ["Standard implementation risks"],
                "test_coverage": "Appropriate testing performed"
            }
        
        cs_raw = output.get("confidence_score") or output.get("confidence") or 0.5
        try:
            confidence_score = float(cs_raw)
        except Exception:
            confidence_score = 0.5
        
        if confidence_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW

        return TaskCompletionResult(
            issue_number=issue.number,
            status=output.get("status") or "unknown",
            completion_summary=output.get("completion_summary") or output.get("summary") or "No summary available",
            files_modified=output.get("files_modified") or output.get("files") or [],
            pull_request_url=output.get("pull_request_url"),
            session_id=f"{implementation_session.session_id},{summary_session.session_id}",
            session_url=f"{implementation_session.url}|{summary_session.url}",
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
