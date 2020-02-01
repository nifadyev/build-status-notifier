"""Script for running Drone CI check in the background."""

import json
import time
import requests
# import slack
from src.ci_systems.drone import Drone
from src.notifiers.slack import Slack


# # ! MAIN
# # TODO: add base abstract class for all ci_systems
# API = 'https://drone-github.skyscannertools.net/api/repos/quotes-and-data-services/'
# AUTHOR = 'artezio-vnifadiev'
# CHANNEL = 'DP7AHFC13'  # ID for direct messages
# FREQUENCY = 30  # Seconds between request to Drone CI API

# Load user credentials
with open('./config.json') as conf:
    # TODO: Also load from config AUTHOR and CHANNEL
    CONFIG = json.load(conf)
    SLACKBOT_TOKEN = CONFIG['slackbot_token']

DRONE = Drone()
# ! MAIN
print('Bot is running\n')

# ! SLACK
# @slack.RTMClient.run_on(event='message')
# def listen(**payload):
#     """Listen to bot for incoming messages.

#     param: payload - 

#     returns: None
#     """
#     print('message received\n')
#     data = payload['data']
#     web_client = payload['web_client']
#     command_and_args = data.get('text', []).split()
#     print(command_and_args)

#     # Only messages like 'monitor skippy' are supported
#     # This check fixes Exception after notifying about finished builds
#     # But later it should be improved
#     if len(command_and_args) == 2:
#         DRONE.execute_command(web_client=web_client, command=command_and_args[0], args=command_and_args[1:])

# ! MAIN
# Check if there are active builds
# ! ATM only one repo at a program instance
# initial_integrations_builds = get_running_builds('integrations', author=AUTHOR)
# initial_skippy_builds = get_running_builds('skippy-integrations', author=AUTHOR)

# if initial_integrations_builds:
#     monitor_active_builds(repository='integrations', author=AUTHOR)
# elif initial_skippy_builds:
#     monitor_active_builds(repository='skippy-integrations', author=AUTHOR)


# ! MAIN
if __name__ == "__main__":
    ci_system = Drone()
    notifier = Slack(SLACKBOT_TOKEN, ci_system)
    notifier.start()
    # rtm_client = slack.RTMClient(token=SLACKBOT_TOKEN)
    # rtm_client.start()
