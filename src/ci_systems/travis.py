"""Module for dealing with Travis CI API."""

import time
from typing import Dict, Any, List, Tuple, Optional

import requests
from requests import Response

from ..notifiers.slack import Slack
from ..custom_types import BUILD


class Travis():
    """Class for sending requests via Travis API and parsing their response."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize class instance.

        Args:
            config: Travis API specific credentials.

        Attributes:
            token: unique key.
            author: author alias.
            repository_id: repository ID in Travis.
            frequency: interval in seconds between consecutive requests to API.
        """
        self.token = config['token']
        self.author = config['author']['login']
        self.repository_id = config['repositories'][0]['id']
        self.frequency = config['request_frequency']

    def execute_command(self, command: str, args: List = None) -> None:
        """Execute supported command with optional arguments.

        Args:
            command: valid keyword.
            args: optional arguments for some commands.
        """
        if command == 'monitor':
            print(f'Executing command {command} {args or ""}')
            self.monitor_builds()
        else:
            print('Unsupported command')

    def monitor_builds(self) -> None:
        """Check build statuses for specified author and repository with set frequency.

        Check if there are any active builds of specific author.
        If yes, run endless loop until all active builds are finished.
        """
        initial_builds = self.get_builds_in_progress()

        if not initial_builds:
            print('There are no builds in progress')
            return

        while True:
            builds_in_progress = self.get_builds_in_progress()

            print(f'{len(builds_in_progress)} builds are still in progress')
            if builds_in_progress == initial_builds:
                time.sleep(self.frequency)
                continue

            for build in self.get_finished_builds(initial_builds, builds_in_progress):
                is_build_finished = self.handle_build(build)
                if not is_build_finished:
                    continue

            if not builds_in_progress:
                print('Finishing monitoring')
                Slack.notify(message='All builds are finished')
                break

            initial_builds = builds_in_progress
            time.sleep(self.frequency)

    def get_builds_in_progress(self) -> Tuple[BUILD]:
        """Return list of active builds for specified repository and author.

        Build is active if its status is `created` or `started`.

        Returns:
            tuple: sequence of active author's builds.
        """
        request = self.request_factory(f'repo/{self.repository_id}/builds')
        builds = request.json()['builds']

        return tuple(
            self.parse_build(build) for build in builds if self._is_build_in_progress(build))

    def _is_build_in_progress(self, build: Dict[str, Any]) -> bool:
        """Check build status and author.

        Args:
            build: raw information about build from response.

        Returns:
            bool: indicates if build is in progress.
        """
        return (
            build['created_by']['login'] == self.author
            and build['state'] in ('started', 'created', 'pending', 'running')
        )

    def handle_build(self, build: BUILD) -> bool:
        """Deal with build and call Slack method if build is finished.

        Arguments:
            build: necessary information about build.

        Returns:
            bool: indicates if message is sent successfully.
        """
        build_response = self.request_factory(f'build/{build["id"]}')
        build = self.parse_build(build=build_response.json())

        # Do not send message if build status has changed from `created` to `started`
        if build['status'] in ('started', 'created', 'pending', 'running'):
            return False

        if build['status'] == 'failed':
            jobs_response = self.request_factory(f'build/{build["id"]}/jobs')
            failed_job_id = self.get_failed_job_id(jobs_response.json())

            log_response = self.request_factory(f'job/{failed_job_id}/log')
            log = log_response.json()['content']
            # Last 3 strings are useless
            error_strings = log.splitlines()[-8:-3]

            status_code = Slack.notify(build, error_strings, failed_job_id)
        else:
            status_code = Slack.notify(build)

        return status_code == '200'

    @staticmethod
    def get_finished_builds(
            initial_builds: Tuple[BUILD], builds_in_progress: Tuple[BUILD]) -> Tuple[BUILD]:
        """Return finished builds by comparing builds in progress with initial builds.

        Args:
            initial_builds: sequence of initial builds.
            builds_in_progress: sequence of builds in progress.

        Returns:
            tuple: sequence of finished builds.
        """
        return tuple(build for build in initial_builds if build not in builds_in_progress)

    @staticmethod
    def parse_build(build: Dict) -> BUILD:
        """Retrieve necessary information from raw build response.

        Arguments:
            build: raw response.

        Returns:
            dict: necessary information about build.
        """
        return {
            'id': build['id'],
            'event': build['event_type'],
            'status': build['state'],
            'branch': build['branch']['name'],
            'message': build['commit']['message'],
            'duration': build['duration'],
            'pr_url': build['commit']['compare_url'],
            'commit_sha': build['commit']['sha']
        }

    @staticmethod
    def get_failed_job_id(jobs: Dict) -> Optional[str]:
        """Return ID of failed Travis job.

        Args:
            jobs: information about all build jobs.

        Returns:
            str: job ID.
        """
        for job in jobs['jobs']:
            if job['state'] == 'failed':
                return job['id']

    def request_factory(self, path: str) -> Response:
        """Make request to Travis API with provided path.

        Args:
            path: path to specific resource.

        Returns:
            Response: response from API.
        """
        return requests.get(
            f'https://api.travis-ci.com/{path}',
            headers={
                'Travis-API-Version': '3',
                'User-Agent': 'API Explorer',
                'Authorization': f'token {self.token}'
            }
        )
