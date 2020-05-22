"""Module for testing basic bot functions."""

import json
from unittest import mock
import pytest

import bot
import src.ci_systems.travis as travis
from src.ci_systems.travis import Travis
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
    # @pytest.mark.skip
    def test_travis_builds_are_passed(self):
        travis.requests = mock.Mock()

        with open('tests/travis_examples/running_builds.json') as initial_builds, \
                open('tests/travis_examples/finished_builds_passed.json') as finished_build, \
                open('tests/travis_examples/passed_build.json') as passed_build:

            travis.requests.get.side_effect = [
                MockResponse(json.load(initial_builds), 200),
                MockResponse(json.load(finished_build), 200),
                MockResponse(json.load(passed_build), 200),
            ]

        bot.run_bot(Travis, Slack)

    @pytest.mark.skip
    def test_travis_build_has_failed(self):
        travis.requests = mock.Mock()

        with open('tests/travis_examples/running_builds.json') as initial_builds, \
                open('tests/travis_examples/finished_builds_failed.json') as finished_build, \
                open('tests/travis_examples/failed_build.json') as failed_build, \
                open('tests/travis_examples/1_failed_job.json') as failed_jobs, \
                open('tests/travis_examples/failed_job_log.json') as failed_job_log:

            travis.requests.get.side_effect = [
                MockResponse(json.load(initial_builds), 200),
                MockResponse(json.load(finished_build), 200),
                MockResponse(json.load(failed_build), 200),
                MockResponse(json.load(failed_jobs), 200),
                MockResponse(json.load(failed_job_log), 200),
            ]

        bot.run_bot(Travis, Slack)
