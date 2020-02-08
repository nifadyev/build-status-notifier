"""Module for sending messages to Slack channels."""
import requests
import json
from typing import Callable, Dict, Any
from slack import RTMClient, WebClient


with open('/home/nifadyev/code/build-status-notifier/config.json') as conf:
    CONFIG = json.load(conf)
    SLACKBOT_TOKEN = CONFIG['slack']['token']

class Slack(RTMClient):
    """Class for sending messages and listening to them via Slack API."""

    def __init__(self, token: str, ci_system: Callable) -> None:
        """Initialize class instance and listen to incoming messages.

        Args:
            token: Slack Bot unique token.
            ci_system: Instance of Drone, Travis or Jenkins class.
        """
        super(Slack, self).__init__(token=token)
        self.ci_system = ci_system

        self.on(event='message', callback=self.listen)

    def listen(self, **payload: Dict[str, Any]) -> None:
        """Listen for incoming messages and handle them using external functions.

        Args:
            payload - The initial state returned when establishing an RTM connection.
        """
        # TODO: Replace to logger and print received message
        print('message received\n')

        data = payload['data']
        web_client = payload['web_client']
        command_and_args = data.get('text', []).split()


        # Only messages like 'monitor skippy' are supported
        # This check fixes Exception after notifying about finished builds
        # But later it should be improved
        if len(command_and_args) == 2:
            self.ci_system.execute_command(web_client, *command_and_args)

    @staticmethod
    def get_message_header(build: Dict[str, Any]) -> str:
        """Return message header based on build type.

        Args:
            build: dict with information about build.

        Returns:
            str: human representation of build status and what type of build was finished.
        """
        if build['event'] == 'pull_request':
            return 'Pull request check has been completed'
        if build['event'] == 'push' and build['branch'] == 'master':
            return 'Merge check has been completed'
        if build['event'] == 'push':
            return 'Feature branch check has been completed'

        return 'Unsupported type of event'

    @staticmethod
    def make_message(build: Dict[str, Any]) -> str:
        """Create informative message about the build's status.

        Args:
            build: dict with information about build.

        Returns:
            str: detailed information about build execution.
        """
        # TODO: Add extra info for failed builds
        execution_time = build['finished_at'] - build['started_at']
        execution_time_minutes = execution_time // 60
        execution_time_seconds = execution_time % 60
        message_header = Slack.get_message_header(build)

        return (
            f'{message_header}\n\n'
            f"Commit: {build['message']}\n"
            f"Status: {build['status']}\n"
            f"Execution time: {execution_time_minutes} minutes "
            f"{execution_time_seconds} seconds"
        )

    @staticmethod
    def send_message(web_client: WebClient, channel_id: str, message: str) -> bool:
        """Send message to channel using provided WebClient and return request status.

        Args:
            web_client: Slack web client.
            channel_id: Slack channel ID.
            message: message to be sent.

        Returns:
            bool: True or False request execution status.
        """
        if web_client:
            response = web_client.chat_postMessage(
                channel=channel_id,
                text=message
            )

            return response['ok']
        # return False
        # * For now web_client is always passed
        # ! Except for testing purposes
        else:
            response = requests.post(
                url='https://slack.com/api/chat.postMessage',
                json={"channel": "DP7AHFC13", "text": message},
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {SLACKBOT_TOKEN}"
                }
            )

            return response.status_code == '200'
