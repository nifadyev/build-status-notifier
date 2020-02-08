"""Module for testing basic bot functions."""

import pytest
import json
from unittest import mock
from src.ci_systems.drone import Drone
import src.ci_systems.drone as drone
from src.notifiers.slack import Slack


with open('/home/nifadyev/code/build-status-notifier/config.json') as conf:
    CONFIG = json.load(conf)

INITIAL_BUILDS = [
    {
        "id": 2935643,
        "number": 23998,
        "event": "push",
        "status": "running",
        "error": "",
        "enqueued_at": 1570708482,
        "started_at": 1570708483,
        "finished_at": 0,
        "message": "Merge pull request #3481 from quotes-and-data-services/FDA-33550\n\nAdd another one error to known errors mapping",
        "author": "artezio-olgas",
        "link_url": "https://github.skyscannertools.net/quotes-and-data-services/integrations/commit/cbe8ec4d269b465b6e24e3b36fffcd7905853b00",
        "branch": "master",
    },
]

FINISHED_BUILDS = [
    {
        "id": 2935643,
        "number": 23998,
        "event": "push",
        "status": "success",
        "error": "",
        "started_at": 1570708483,
        "finished_at": 1570708596,
        "message": "Merge pull request #3481 from quotes-and-data-services/FDA-33550\n\nAdd another one error to known errors mapping",
        "author": "artezio-olgas",
        "link_url": "https://github.skyscannertools.net/quotes-and-data-services/integrations/commit/cbe8ec4d269b465b6e24e3b36fffcd7905853b00",
        "branch": "master",
    },
]

DETAILED_FINISHED_BUILD = {
    "status": "success",
    "started_at": 1570708483,
    "finished_at": 1570708596,
    "event": "push",
    "branch": "master",
    "message": "Merge pull request #3481 from quotes-and-data-services/FDA-33550\n\nAdd another one error to known errors mapping",
}


class MockResponse:
    """Class for mocking requests.get method and it's attributes."""

    def __init__(self, json_data, status_code=200):
        self.content = json_data
        self.status_code = status_code

    def json(self):
        """Return JSON response's representation."""

        return self.content


class TestDrone:

    # * Some kind of smoke test
    def test_monitor_builds(self):
        drone.requests = mock.Mock()
        # TODO: Return Slack like response
        Slack.send_message = mock.Mock()

        side_effects = [
            MockResponse(INITIAL_BUILDS, 200),
            MockResponse(FINISHED_BUILDS, 200),
            MockResponse(DETAILED_FINISHED_BUILD, 200)
        ]
        drone.requests.get.side_effect = side_effects
        # import pdb; pdb.set_trace()
        drone_instance = Drone(CONFIG)

        drone_instance.monitor_active_builds(web_client=None, author=CONFIG['drone']['author'])
