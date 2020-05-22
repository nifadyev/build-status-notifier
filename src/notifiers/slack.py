"""Module for handling requests to Slack API."""

import json
from typing import Callable, Dict, Any, List, Union

import requests
from slack import RTMClient

from .message_templates import BRANCH_SUCCESS_BLOCKS, BRANCH_FAIL_BLOCKS
from ..custom_types import MESSAGE, BUILD


# Global credentials allow to call some methods as static in CI systems modules
with open('config.json') as conf:
    CONFIGURATION = json.load(conf)

    SLACKBOT_TOKEN = CONFIGURATION['slack']['token']
    CHANNEL_ID = CONFIGURATION['slack']['bot_direct_messages_id']


class Slack(RTMClient):
    """Class for sending messages and listening to them via Slack API."""

    def __init__(self, config: Dict[str, str], ci_system: Callable) -> None:
        """Initialize class instance and listen to incoming messages.

        Args:
            config: Slack API specific credentials.
            ci_system: Travis class instance for calling static method.
        """
        super(Slack, self).__init__(token=config['token'])

        self.token = config['token']
        self.ci_system = ci_system

        self.on(event='message', callback=self.listen)

    def listen(self, **payload: Dict[str, Any]) -> None:
        """Listen for incoming messages and handle them using external functions.

        Args:
            payload - The initial state returned when establishing an RTM connection.
        """
        command_and_args = payload['data'].get('text', '').split()

        # Supported message format: <command> <repository>
        # This check fixes Exception after notifying about finished builds
        if len(command_and_args) == 2:
            self.ci_system.execute_command(*command_and_args)

    @staticmethod
    def notify(
            build: BUILD = None,
            error_strings: List[str] = None,
            failed_job_id: str = None,
            message: str = None
    ) -> str:
        """Compose suitable message and send it to specified channel.

        Keyword Args:
            build: necessary information about build.
            error_strings: last lines of job log with useful information about fail.
            failed_job_id: ID for composing valid link to failed job.
            message: simple plain text with non build specific information.

        Returns:
            str: response HTTP code from method _send_message().
        """
        if not build and message:
            blocks = message
        elif build and error_strings and failed_job_id:
            blocks = Slack._make_failure_message(build, error_strings, failed_job_id)
        elif build:
            blocks = Slack._make_success_message(build)

        status_code = Slack._send_message(blocks)

        return status_code

    @staticmethod
    def _make_failure_message(
            build: BUILD, error_strings: List[str], failed_job_id: str) -> MESSAGE:
        """Fill blocks template with information about failed build.

        Logs and failed Travis Job link are included for such builds.

        Args:
            build: necessary information about build.
            error_strings: last lines of job log with useful information about fail.
            failed_job_id: ID for composing valid link to failed job.

        Returns:
            list: detailed information about build execution.
        """
        message = Slack._make_common_message(build, is_failed=True)
        less_log = '\n'.join(string for string in error_strings)

        message[1]['text']['text'] = (
            f'{message[1]["text"]["text"]}*Log (last 3 strings)*:\n ```{less_log}``` \n')
        message[2]['elements'][1]['url'] = (
            f'https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/{failed_job_id}')

        return message

    @staticmethod
    def _make_success_message(build: BUILD) -> MESSAGE:
        """Fill blocks template with information about successful build.

        Pull request link is included for such builds.

        Args:
            build: necessary information about build.

        Returns:
            list: detailed information about build execution.
        """
        message = Slack._make_common_message(build)
        message[2]['elements'][1]['url'] = (
            'https://github.com/nifadyev/cubic-spline-interpolator/compare/'
            f'{build["branch"]}?expand=1'
        )

        return message

    @staticmethod
    def _make_common_message(build: BUILD, is_failed: bool = False) -> MESSAGE:
        """Fill blocks template with common information about build.

        Args:
            build: necessary information about build.
            is_failed: indicates failed build.

        Returns:
            list: detailed information about build execution.
        """
        message = BRANCH_FAIL_BLOCKS.copy() if is_failed else BRANCH_SUCCESS_BLOCKS.copy()

        message[1]['text']['text'] = (
            f'*Branch:*\n {build["branch"]} \n'
            f'*Commit:*\n {build["message"]} \n'
            f'*Duration:*\n {build["duration"] // 60} minutes {build["duration"] % 60} seconds \n'
        )
        message[2]['elements'][0]['url'] = (
            f'https://github.com/nifadyev/cubic-spline-interpolator/commit/{build["commit_sha"]}')

        return message

    @staticmethod
    def _send_message(message: Union[MESSAGE, str]) -> str:
        """Send message to specified channel and return request status.

        Send blocks for rich-text message and plain text to be used as Slack desktop notification.

        Args:
            message: filled blocks template or plain text.

        Returns:
            str: response HTTP code.
        """
        notification_text = message[0]['text']['text'] if isinstance(message, list) else message
        response = requests.post(
            url='https://slack.com/api/chat.postMessage',
            json={
                'channel': CHANNEL_ID,
                'text': notification_text,
                'blocks': message
            },
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {SLACKBOT_TOKEN}'
            }
        )

        return response.status_code
