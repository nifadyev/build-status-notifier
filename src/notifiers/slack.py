"""Module for sending messages to Slack channels."""

import json
from typing import Callable, Dict, Any
import requests

from slack import RTMClient

from .message_templates import BRANCH_SUCCESS_BLOCKS, BRANCH_FAIL_BLOCKS


# Global credentials allow to call some methods as static in CI systems modules
with open('config.json') as conf:
    CONFIG = json.load(conf)

    SLACKBOT_TOKEN = CONFIG['slack']['token']
    CHANNEL_ID = CONFIG['slack']['bot_direct_messages_id']


class Slack(RTMClient):
    """Class for sending messages and listening to them via Slack API."""

    def __init__(self, config, ci_system: Callable) -> None:
        """Initialize class instance and listen to incoming messages.

        Args:
            config: dict with specific Slack API credentials.
            ci_system: Travis class instance.
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
        print('message received\n')

        data = payload['data']
        command_and_args = data.get('text', '').split()

        # Supported message format: <command> <repository>
        # This check fixes Exception after notifying about finished builds
        if len(command_and_args) == 2:
            self.ci_system.execute_command(*command_and_args)

    @staticmethod
    def _make_common_message(build, is_failed=False):
        """Create informative message about the build's status.

        def make_message(build: Dict[str, Any]) -> List:
        Args:
            build: dict with information about build.

        Returns:
            str: detailed information about build execution.
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
    def _make_success_message(build):
        message = Slack._make_common_message(build)
        message[2]['elements'][1]['url'] = build['pr_url']

        return message

    @staticmethod
    def _make_failure_message(build, error_strings, failed_job_id):
        message = Slack._make_common_message(build, is_failed=True)
        less_log = '\n'.join(string for string in error_strings)

        message[1]['text']['text'] = (
            f'{message[1]["text"]["text"]}*Log (last 3 strings)*:\n ```{less_log}``` \n')
        message[2]['elements'][1]['url'] = (
            f'https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/{failed_job_id}')

        return message

    @staticmethod
    def _send_message(message):
        """Send message to channel using provided WebClient and return request status.

        Args:
            channel_id: Slack channel ID.
            message: message to be sent.

        Returns:
            bool: True or False request execution status.
        """
        preview_notification_text = (
            message[0]['text']['text'] if isinstance(message, list) else message)
        response = requests.post(
            url='https://slack.com/api/chat.postMessage',
            json={
                'channel': CHANNEL_ID,
                # Used as preview for desktop notifications
                'text': preview_notification_text,
                'blocks': message
            },
            headers={
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {SLACKBOT_TOKEN}'
            }
        )

        print(f'sent status: {response.status_code}')
        print(response.text)

        # ! Ignore invalid block formats
        return response.status_code == '200'

    @staticmethod
    def notify(build=None, error_strings=None, failed_job_id=None, message=None):
        if not build and message:
            blocks = message
        elif error_strings and failed_job_id:
            blocks = Slack._make_failure_message(build, error_strings, failed_job_id)
        else:
            blocks = Slack._make_success_message(build)

        Slack._send_message(blocks)
