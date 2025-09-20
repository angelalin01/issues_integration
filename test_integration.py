#!/usr/bin/env python3

import asyncio
import os
from github_client import GitHubClient
from devin_client import DevinClient
from config import Config

async def test_github_integration():
    """Test GitHub API integration"""
    print("Testing GitHub integration...")
    
    try:
        github_client = GitHubClient()
        
        test_repo = "octocat/Hello-World"
        print(f"Fetching issues from {test_repo}...")
        
        issues = github_client.list_issues(test_repo, limit=5)
        print(f"✅ Successfully fetched {len(issues)} issues")
        
        if issues:
            issue = issues[0]
            print(f"Sample issue: #{issue.number} - {issue.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub integration failed: {str(e)}")
        return False

async def test_devin_integration():
    """Test Devin API integration"""
    print("\nTesting Devin integration...")
    
    try:
        devin_client = DevinClient()
        
        print("Creating test Devin session...")
        session = await devin_client.create_session("Hello, this is a test session. Please respond with 'Test successful'.")
        
        print(f"✅ Successfully created session: {session.session_id}")
        print(f"Session URL: {session.url}")
        
        print("⏳ Session created successfully (not waiting for completion in test)")
        
        return True
        
    except Exception as e:
        print(f"❌ Devin integration failed: {str(e)}")
        return False

async def main():
    """Run integration tests"""
    print("🚀 GitHub Issues Integration - Testing Components\n")
    
    print("Checking configuration...")
    try:
        Config.validate()
        print("✅ Configuration valid")
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file with DEVIN_API_KEY and GITHUB_TOKEN")
        print("2. Set valid API keys")
        return
    
    github_success = await test_github_integration()
    
    devin_success = await test_devin_integration()
    
    print(f"\n📊 Test Results:")
    print(f"GitHub Integration: {'✅ PASS' if github_success else '❌ FAIL'}")
    print(f"Devin Integration: {'✅ PASS' if devin_success else '❌ FAIL'}")
    
    if github_success and devin_success:
        print("\n🎉 All tests passed! The integration is ready to use.")
        print("\nTry running:")
        print("python main.py list-issues --repo octocat/Hello-World")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")

if __name__ == "__main__":
    asyncio.run(main())
