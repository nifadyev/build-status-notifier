"""Module for testing basic bot functions."""

import sys
import pytest
import bot
from src.ci_systems.drone import Drone
from src.notifiers.slack import Slack


class MockResponse:
    """Class for mocking requests.get method and it's attributes."""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Return JSON response's representation."""

        return self.json_data


class TestBot:

    # * Some kind of smoke test
    def test_drone(self, mocker):

        # bot.load_config = mocker.Mock()

        trello.requests = mocker.Mock()

        with open('/home/nifadyev/code/build-status-notifier/tests/drone_ci_examples/initial_builds_integrations.json') as initial_builds, \
                open('/home/nifadyev/code/build-status-notifier/tests/drone_ci_examples/one_build_is_finished_integrations.json') as builds_with_one_finished_build, \
                open('/home/nifadyev/code/build-status-notifier/tests/drone_ci_examples/finished_build_integrations.json') as finished_build:

        trello.requests.get.return_value = MockResponse(tickets, 200)

        bot.run_bot(Drone, Slack)
        
        # TODO: manually send message
        # requests.post(
        #     url='https://slack.com/api/chat.postMessage',
        #     json={"channel": "DP7AHFC13", "text": message},
        #     headers={
        #         "Content-Type": "application/json; charset=utf-8",
        #         "Authorization": f"Bearer {SLACKBOT_TOKEN}"
        #     }
        # )

        # TODO: terminate bot using os or smth else
        sys.exit()
