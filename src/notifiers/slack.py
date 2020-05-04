"""Module for sending messages to Slack channels."""
import json
from typing import Callable, Dict, Any, List
import requests

from slack import RTMClient

from .message_templates import BRANCH_SUCCESS_BLOCKS, BRANCH_FAIL_BLOCKS


with open('config.json') as conf:
    CONFIG = json.load(conf)

    SLACKBOT_TOKEN = CONFIG['slack']['token']
    CHANNEL_ID = CONFIG['slack']['bot_direct_messages_id']


class Slack(RTMClient):
    """Class for sending messages and listening to them via Slack API."""

    def __init__(self, config, ci_system: Callable) -> None:
        """Initialize class instance and listen to incoming messages.

        Args:
            token: Slack Bot unique token.
            ci_system: Instance of Drone, Travis or Jenkins class.
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
        # ! Check why default value is list
        print(data.get('text'))
        command_and_args = data.get('text', []).split()

        # Only messages like 'monitor skippy' are supported
        # This check fixes Exception after notifying about finished builds
        if len(command_and_args) == 2:
            self.ci_system.execute_command(*command_and_args)

    # TODO: Accept only event and branch (or flag is_merge_commit)
    @staticmethod
    def get_message_header(build: Dict[str, Any]) -> str:
        """Return message header based on build type.

        Args:
            build: dict with information about build.

        Returns:
            str: human representation of build status and what type of build was finished.
        """
        # TODO: use message template
        message_template = '{event} check has been {status}'

        if build['event'] == 'pull_request':
            return 'Pull request check has been completed'
        if build['event'] == 'push' and build['branch'] == 'master':
            return 'Merge check has been completed'
        if build['event'] == 'push':
            return 'Feature branch check has been completed'

        return 'Unsupported type of event'

    @staticmethod
    def make_message(build: Dict[str, Any]) -> List:
        """Create informative message about the build's status.

        Args:
            build: dict with information about build.

        Returns:
            str: detailed information about build execution.
        """
        message = BRANCH_SUCCESS_BLOCKS.copy()

        message[1]['text']['text'] = (
            f'*Branch:*\n {build["branch"]} \n'
            f'*Commit:*\n {build["message"]} \n'
            f'*Duration:*\n {build["duration"] // 60} minutes {build["duration"] % 60} seconds \n'
        )
        message[2]['elements'][0]['url'] = (
            f'https://github.com/nifadyev/cubic-spline-interpolator/commit/{build["commit_sha"]}')
        message[2]['elements'][1]['url'] = build['pr_url']

        return message

    @staticmethod
    def make_failure_message(build: Dict[str, Any], error_strings, failed_job_id) -> List:
        # ! Duplicates method make_message() except Job URL (instead of PR URL)
        less_log = '\n'.join(string for string in error_strings)
        message = BRANCH_FAIL_BLOCKS.copy()

        message[1]['text']['text'] = (
            f'*Branch:*\n {build["branch"]} \n'
            f'*Commit:*\n {build["message"]} \n'
            f'*Duration:*\n {build["duration"] // 60} minutes {build["duration"] % 60} seconds \n'
            f'*Log (last 3 strings)*:\n ```{less_log}``` \n'
        )
        message[2]['elements'][0]['url'] = (
            f'https://github.com/nifadyev/cubic-spline-interpolator/commit/{build["commit_sha"]}')
        message[2]['elements'][1]['url'] = (
            f'https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/{failed_job_id}')

        return message

    # def _ma

    # ? Init token and channel_id as globals
    @staticmethod
    def send_message(message) -> bool:
        """Send message to channel using provided WebClient and return request status.

        Args:
            channel_id: Slack channel ID.
            message: message to be sent.

        Returns:
            bool: True or False request execution status.
        """
        response = requests.post(
            url='https://slack.com/api/chat.postMessage',
            json={"channel": CHANNEL_ID, "blocks": message},
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {SLACKBOT_TOKEN}"
            }
        )

        print(f'sent status: {response.status_code}')
        print(response.text)

        # ! Ignore invalid block formats
        return response.status_code == '200'
