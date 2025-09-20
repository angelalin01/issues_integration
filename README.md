# GitHub Issues Integration with Devin

This automation integrates Devin with GitHub Issues to provide:

1. **Issue Listing**: View GitHub issues in a dashboard or CLI
2. **Issue Scoping**: Trigger Devin sessions to analyze issues and assign confidence scores
3. **Task Completion**: Trigger Devin sessions to complete issues based on action plans

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the CLI tool:
   ```bash
   python main.py --help
   ```

## Usage

### List Issues
```bash
python main.py list-issues --repo owner/repo
```

### Scope Issue
```bash
python main.py scope-issue --repo owner/repo --issue-number 123
```

### Complete Issue
```bash
python main.py complete-issue --repo owner/repo --issue-number 123
```

### Dashboard Mode
```bash
python main.py dashboard --repo owner/repo
```

## Configuration

- `DEVIN_API_KEY`: Your Devin API key
- `GITHUB_TOKEN`: GitHub personal access token
- `DEVIN_API_BASE`: Devin API base URL (default: https://api.devin.ai/v1)
