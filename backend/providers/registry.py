"""Provider factory — creates the right provider from config."""

from __future__ import annotations

from .base import TicketProvider
from .jira_provider import JiraProvider
from .azure_provider import AzureDevOpsProvider
from .github_provider import GitHubProvider


def get_provider(config: dict) -> TicketProvider:
    """Create a ticket provider based on the config's 'provider' field."""
    name = config.get("provider", "").lower()

    if name == "jira":
        return JiraProvider(
            base_url=config["jira_url"],
            email=config["jira_email"],
            api_token=config["jira_token"],
        )
    elif name == "azure":
        return AzureDevOpsProvider(
            org_url=config["azure_org_url"],
            project=config["azure_project"],
            pat=config["azure_pat"],
        )
    elif name == "github":
        return GitHubProvider(
            token=config["github_token"],
            owner=config["github_owner"],
            repo=config["github_repo"],
        )
    else:
        raise ValueError(f"Unknown provider: {name!r}. Use 'jira', 'azure', or 'github'.")
