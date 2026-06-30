from notifier.application import interfaces
from notifier.application.services import RenderService


class SendIssue:
    def __init__(
        self,
        provider: interfaces.GitProvider,
        notifiers: list[interfaces.Notifier],
        render_service: RenderService,
    ) -> None:
        self._provider = provider
        self._notifiers = notifiers
        self._render_service = render_service

    def handler(self) -> None:
        issue = self._provider.get_issue()
        labels = self._render_service.format_labels(issue.labels)
        body = self._render_service.format_body(issue.body)

        for notifier in self._notifiers:
            notifier.send_issue(issue, body, labels)


class SendPR:
    def __init__(
        self,
        provider: interfaces.GitProvider,
        notifiers: list[interfaces.Notifier],
        render_service: RenderService,
    ) -> None:
        self._provider = provider
        self._notifiers = notifiers
        self._render_service = render_service

    def handler(self) -> None:
        pr = self._provider.get_pull_request()
        labels = self._render_service.format_labels(pr.labels)
        body = self._render_service.format_body(pr.body)

        for notifier in self._notifiers:
            notifier.send_pull_request(pr, body, labels)
