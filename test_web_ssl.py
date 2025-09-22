#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('.')

from devin_client import DevinClient
from models import GitHubIssue

def test_web_server_ssl_pathway():
    """Test SSL connection using the same pathway as web server"""
    
    mock_issue = GitHubIssue(
        number=123,
        title="Test SSL via web server pathway",
        body="Testing SSL certificate verification through web server code path",
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
        print("=== Testing Web Server SSL Pathway ===")
        print("Simulating web server's SSL connection approach...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print("Creating DevinClient in new event loop...")
            devin_client = DevinClient()
            
            print("Attempting scope_issue call (this should trigger SSL error if it exists)...")
            scope_result = loop.run_until_complete(devin_client.scope_issue(mock_issue))
            
            print("SUCCESS: Web server SSL pathway completed without errors")
            print(f"Session URL: {scope_result.session_url}")
            print(f"Confidence Score: {scope_result.confidence_score}")
            return True
            
        finally:
            loop.close()
            print("Event loop closed")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        
        error_str = str(e)
        if "SSLCertVerificationError" in error_str or "certificate verify failed" in error_str:
            print("CONFIRMED: SSL certificate verification error reproduced via web server pathway!")
            if "unable to get local issuer certificate" in error_str:
                print("EXACT MATCH: Same error as user reported!")
            return False
        elif "ssl" in error_str.lower():
            print("SSL-related error detected (but not certificate verification)")
            return False
        else:
            print("Non-SSL error occurred")
            return False

if __name__ == "__main__":
    test_web_server_ssl_pathway()
