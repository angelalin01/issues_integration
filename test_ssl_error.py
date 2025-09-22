#!/usr/bin/env python3

import asyncio
import os
from devin_client import DevinClient
from models import GitHubIssue

async def test_devin_ssl():
    """Test direct Devin API call to reproduce SSL certificate verification error"""
    
    mock_issue = GitHubIssue(
        number=123,
        title="Test SSL certificate verification",
        body="This is a test issue to reproduce SSL certificate verification error",
        state="open",
        labels=[],
        assignees=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        html_url="https://github.com/test/repo/issues/123",
        url="https://api.github.com/repos/test/repo/issues/123",
        repository="test/repo"
    )
    
    try:
        print("Testing Devin API SSL connection...")
        print(f"Using DEVIN_API_KEY prefix: {os.getenv('DEVIN_API_KEY', 'NOT_SET')[:6]}...")
        
        client = DevinClient()
        print("DevinClient created successfully")
        
        print("Attempting to scope issue (this should trigger SSL error if it exists)...")
        result = await client.scope_issue(mock_issue)
        
        print("SUCCESS: Devin API call completed without SSL errors")
        print(f"Session URL: {result.session_url}")
        return True
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        
        if "SSLCertVerificationError" in str(e) or "certificate verify failed" in str(e):
            print("CONFIRMED: SSL certificate verification error reproduced!")
            return False
        elif "ssl" in str(e).lower():
            print("SSL-related error detected (but not certificate verification)")
            return False
        else:
            print("Non-SSL error occurred")
            return False

if __name__ == "__main__":
    asyncio.run(test_devin_ssl())
