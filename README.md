# GitHub Issues Integration with Devin

This automation integrates Devin with GitHub Issues to provide:

1. **Issue Listing**: View GitHub issues in a dashboard or CLI
2. **Issue Scoping**: Trigger Devin sessions to analyze issues and assign confidence scores
3. **Task Completion**: Trigger Devin sessions to complete issues based on action plans

## Quick Demo (No Setup Required)

### Option 1: Web Interface Demo (Works in any browser)
Interactive web demo with GitHub-themed interface:
```bash
# Open in your browser
open demo_web.html
# Or on Linux/Windows: double-click demo_web.html
```

### Option 2: Simple CLI Demo (Works with basic Python 3.x)
If you have Python 3.x but don't want to install dependencies:
```bash
python3 simple_demo.py
```

### Option 3: Rich CLI Demo (Requires Python 3.8+)
For rich formatting and full CLI experience:
```bash
python3 demo.py
```

## Full Setup (Python 3.8+ Required)

**Important**: This project requires Python 3.8 or higher. If you're using Python 2.7, please upgrade first.

1. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment file** (optional for demo):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if you want to use real GitHub/Devin APIs
   ```

5. **Run the CLI tool**:
   ```bash
   python main.py --help
   ```

## Usage

### Demo Mode (No API Keys Required)

#### Web Interface Demo
```bash
# Interactive web demo (no dependencies required)
open demo_web.html
```

#### CLI Demo Commands
```bash
# List demo issues
python main.py list-issues --demo --repo test/repo

# Scope demo issue with confidence analysis
python main.py scope-issue --demo --repo test/repo --issue-number 123

# Complete demo issue with pre-scoping
python main.py complete-issue --demo --repo test/repo --issue-number 123 --scope-first

# Interactive demo dashboard
python main.py dashboard --demo --repo test/repo

# Full workflow demos
python demo.py              # Rich CLI demo
python simple_demo.py       # Simple CLI demo
```

### Production Mode (API Keys Required)
```bash
# List real GitHub issues
python main.py list-issues --repo owner/repo

# Scope real issue
python main.py scope-issue --repo owner/repo --issue-number 123

# Complete real issue
python main.py complete-issue --repo owner/repo --issue-number 123

# Interactive dashboard
python main.py dashboard --repo owner/repo
```

### Automatic Fallback
Commands automatically use demo mode with helpful warnings when API credentials are not configured:
```bash
python main.py list-issues --repo octocat/Hello-World
# Output: ⚠️ Using demo mode - API credentials not configured
```

## Configuration

- `DEVIN_API_KEY`: Your Devin API key
- `GITHUB_TOKEN`: GitHub personal access token
- `DEVIN_API_BASE`: Devin API base URL (default: https://api.devin.ai/v1)
