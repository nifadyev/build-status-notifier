"""Module for sending messages to Slack channels."""

import requests
# import slack
from slack.rtm.client import RTMClient as rtm
# from src.ci_systems.drone import Drone

# # TODO: add base abstract class for all ci_systems
# API = 'https://drone-github.skyscannertools.net/api/repos/quotes-and-data-services/'
# AUTHOR = 'artezio-vnifadiev'
# CHANNEL = 'DP7AHFC13'  # ID for direct messages
# FREQUENCY = 30  # Seconds between request to Drone CI API

# # Load user credentials
# with open('../config.json') as conf:
#     # TODO: Also load from config AUTHOR and CHANNEL
#     CONFIG = json.load(conf)
#     DRONE_TOKEN = CONFIG['drone_token']
#     SLACKBOT_TOKEN = CONFIG['slackbot_token']


# ? Use slack.RTMCleint as parent
# Then in main provide token and run method start() from slack.RTMCleint
# class Slack():

class Slack(rtm):

    def __init__(self, token, ci_system):
        super(Slack, self).__init__(token=token)
        self.ci_system = ci_system
        self.on(event='message', callback=self.listen)

    # @rtm.run_on(event='message')
    def listen(self, **payload):
        """Listen to bot for incoming messages.

        param: payload - 

        returns: None
        """
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
    def get_message_header(build):
        """Return message header based on build type."""
        if build['event'] == 'pull_request':
            return 'Pull request check has been completed'
        elif build['event'] == 'push' and build['branch'] == 'master':
            return 'Merge check has been completed'
        elif build['event'] == 'push':
            return 'Feature branch check has been completed'
        else:
            return 'Unsupported type of event'

    @staticmethod
    def make_message(build):
        """Create proper message about the build's status."""
        # TODO: Add extra info for failed builds

        execution_time_minutes = (build['finished_at'] - build['started_at']) // 60
        execution_time_seconds = (build['finished_at'] - build['started_at']) % 60
        message_header = Slack.get_message_header(build)
        message = (
            f'{message_header}\n\n'
            f"Commit: {build['message']}\n"
            f"Status: {build['status']}\n"
            f"Execution time: {execution_time_minutes} minutes "
            f"{execution_time_seconds} seconds"
        )

        return message
