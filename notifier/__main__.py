import os
import re
import sys
import traceback

from notifier.application.interactors import SendIssue, SendPR
from notifier.application.interfaces import Notifier
from notifier.application.services import RenderService
from notifier.infrastructure.discord_gateway import DiscordGateway
from notifier.infrastructure.github_gateway import GithubGateway
from notifier.infrastructure.telegram_gateway import TelegramGateway
from notifier.infrastructure.gitlab_gateway import GitlabGateway

PROVIDERS = [
    (
        (
            r"https://(?:api\.)?github\.com/repos/[\w\-\.]+/[\w\-\.]+/issues/\d+",
            r"https://(?:api\.)?github\.com/repos/[\w\-\.]+/[\w\-\.]+/pulls/\d+",
        ),
        (SendIssue, SendPR),
        GithubGateway,
        "GITHUB_TOKEN",
    ),
    (
        (
            r"https://gitlab\.com/[\w\-.]+/[\w\-.]+/-/issues/\d+",
            r"https://gitlab\.com/[\w\-.]+/[\w\-.]+/-/merge_requests/\d+",
        ),
        (SendIssue, SendPR),
        GitlabGateway,
        "GITLAB_TOKEN",
    ),
]


def get_provider_action(
    url: str,
) -> tuple[
    type[SendIssue] | type[SendPR], type[GithubGateway] | type[GitlabGateway], str
]:
    for variant in PROVIDERS:
        for pattern in range(len(variant[0])):
            if re.match(variant[0][pattern], url):
                return variant[1][pattern], variant[2], variant[3]

    raise ValueError(f"Unknown event type for URL: {url}")


if __name__ == "__main__":
    event_url = os.environ["EVENT_URL"]

    custom_labels = os.environ.get("CUSTOM_LABELS", "").split(",")
    if custom_labels == [""]:
        custom_labels = []

    render_service = RenderService(
        custom_labels=custom_labels,
        join_input_with_list=os.environ.get("JOIN_INPUT_WITH_LIST") == "1",
    )

    notifiers: list[Notifier] = []

    tg_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_bot_token and tg_chat_id:
        html_template = os.environ.get("HTML_TEMPLATE", "").strip()
        telegram_gateway = TelegramGateway(
            chat_id=tg_chat_id,
            bot_token=tg_bot_token,
            attempt_count=int(os.environ.get("ATTEMPT_COUNT", "2")),
            message_thread_id=os.environ.get("TELEGRAM_MESSAGE_THREAD_ID"),
            custom_template=html_template,
        )
        notifiers.append(telegram_gateway)

    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if discord_webhook_url:
        discord_gateway = DiscordGateway(
            webhook_url=discord_webhook_url,
            attempt_count=int(os.environ.get("ATTEMPT_COUNT", "2")),
        )
        notifiers.append(discord_gateway)

    if not notifiers:
        print(
            "Error: No notification platform configured. "
            "Please provide either TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID or DISCORD_WEBHOOK_URL",
            file=sys.stderr,
        )
        sys.exit(1)

    interactor, provider, env_variable = get_provider_action(event_url)
    interactor = interactor(
        provider=provider(
            token=os.environ.get(env_variable) or "", event_url=event_url
        ),
        notifiers=notifiers,
        render_service=render_service,
    )

    try:
        interactor.handler()
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(f"Error processing event: {e}", file=sys.stderr)
        sys.exit(1)
