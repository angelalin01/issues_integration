#!/usr/bin/env python3

import requests
import json

def test_github_token_direct():
    """Test GitHub token authentication directly"""
    
    token = "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"
    repo = "angelalin01/Intent-Extract-NLP-Tasks"
    
    print("=== Testing GitHub Token Authentication ===")
    print(f"Token prefix: {token[:10]}...")
    print(f"Repository: {repo}")
    
    print("\n1. Testing basic authentication (GET /user)...")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Issues-Integration/1.0"
    }
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"Authenticated as: {user_data.get('login', 'Unknown')}")
            print(f"User ID: {user_data.get('id', 'Unknown')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print(f"\n2. Testing repository access (GET /repos/{repo})...")
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            repo_data = response.json()
            print(f"Repository: {repo_data.get('full_name', 'Unknown')}")
            print(f"Private: {repo_data.get('private', 'Unknown')}")
            print(f"Permissions: {repo_data.get('permissions', {})}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print(f"\n3. Testing issues access (GET /repos/{repo}/issues)...")
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}/issues", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            issues = response.json()
            print(f"Found {len(issues)} issues")
            if issues:
                print(f"First issue: #{issues[0].get('number')} - {issues[0].get('title')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print(f"\n4. Testing specific issue access (GET /repos/{repo}/issues/123)...")
    try:
        response = requests.get(f"https://api.github.com/repos/{repo}/issues/123", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            issue = response.json()
            print(f"Issue #{issue.get('number')}: {issue.get('title')}")
            print(f"State: {issue.get('state')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_github_token_direct()
