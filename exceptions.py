class GitHubIssuesIntegrationError(Exception):
    """Base exception for GitHub Issues Integration"""
    pass

class GitHubAPIError(GitHubIssuesIntegrationError):
    """GitHub API related errors"""
    pass

class DevinAPIError(GitHubIssuesIntegrationError):
    """Devin API related errors"""
    pass

class ConfigurationError(GitHubIssuesIntegrationError):
    """Configuration related errors"""
    pass

class ValidationError(GitHubIssuesIntegrationError):
    """Input validation errors"""
    pass

class SessionTimeoutError(DevinAPIError):
    """Devin session timeout errors"""
    pass
