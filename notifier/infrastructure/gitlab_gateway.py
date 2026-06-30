import requests

from notifier.application import interfaces
from notifier.domain.entities import Issue, PullRequest


class GitlabGateway(interfaces.GitProvider):
    def __init__(self, token: str, event_url: str) -> None:
        self._token = token
        self._url = event_url

    def _headers(self) -> dict[str, str]:
        return {
            "PRIVATE-TOKEN": self._token,
        }

    def get_issue(self) -> Issue:
        response = requests.get(self._url, headers=self._headers(), timeout=30)
        response.raise_for_status()

        data = response.json()

        return Issue(
            id=data["iid"],
            title=data["title"],
            labels=[label for label in data.get("labels", [])],
            url=(data.get("web_url") or "").strip(),
            user=data["author"]["username"],
            body=(data.get("description") or "").strip(),
        )

    def get_pull_request(self) -> PullRequest:
        response = requests.get(self._url, headers=self._headers(), timeout=30)
        response.raise_for_status()

        data = response.json()

        return PullRequest(
            id=data["iid"],
            title=data["title"],
            labels=[label for label in data.get("labels", [])],
            url=(data.get("web_url") or "").strip(),
            user=data["author"]["username"],
            body=(data.get("description") or "").strip(),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            head_ref=data["source_branch"],
            base_ref=data["target_branch"],
            repository=data["references"]["full"],
        )
