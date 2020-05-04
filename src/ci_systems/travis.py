"""Module for dealing with Travis CI API."""

import time
from typing import Dict, Any, Union, List, Tuple

import requests

from ..notifiers.slack import Slack
from ..custom_types import CONFIG, MESSAGE, BUILD


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
        self.frequency = config['request_frequency']
        self.repository_id = config['repositories'][0]['id']

    def execute_command(self, command: str, args: List = None) -> None:
        """Execute requested command with optional arguments.

        Args:
            command: valid keyword.
            args: optional arguments for some commands.
        """
        if command == 'monitor':
            print(f'Executing command {command} {args or ""}')
            self.monitor_active_builds()
        else:
            print('Unsupported command')

    def monitor_active_builds(self):
        """Check build statuses for specified author and repository."""
        monitored_builds = self.get_running_builds()

        # Initial check for author's active builds
        if not monitored_builds:
            print('Running builds are not found')
            return

        # Run endless loop till all build are finished
        while True:
            running_builds = self.get_running_builds()
            print(f'{len(running_builds)} builds are are still in progress')

            # Initial builds are still being ran
            # ? Probably too expensive comparison
            if running_builds == monitored_builds:
                time.sleep(self.frequency)
                continue

            for build in self.get_finished_builds(monitored_builds, running_builds):
                # TODO: sep method for processing finished build
                finished_build_response = self.request_factory(f'build/{build["id"]}')
                finished_build = self.parse_build(build=finished_build_response.json())

                # Do not send message if build status has changed from `pending` to `running`
                if finished_build['status'] in ('started', 'created', 'pending', 'running'):
                    continue

                if finished_build['status'] == 'failed':
                    jobs_response = self.request_factory(f'build/{finished_build["id"]}/jobs')
                    failed_job = self.get_failed_job(jobs_response.json())

                    # ! Does not suitable for multiple failed jobs
                    jobs_log_response = self.request_factory(f'job/{failed_job["id"]}/log')
                    jobs_log = jobs_log_response.json()['content']
                    # Last 3 strings are useless, display -8:-3 strings
                    error_strings = jobs_log.splitlines()[-8:-3]

                    Slack.notify(finished_build, error_strings, failed_job['id'])
                else:
                    Slack.notify(finished_build)

            monitored_builds = running_builds

            if not monitored_builds:
                print('Finishing monitoring')
                Slack.notify(message='Running builds are finished')
                # This break does not end endless loop, use some flag to end it (or never end it)
                break

            time.sleep(self.frequency)

    def get_running_builds(self):
        """Return list of active builds for specified repository and author.

        Returns:
            tuple: sequence of active author's builds.
        """
        # Get list of all builds
        request = self.request_factory(f'repo/{self.repository_id}/builds')
        builds = request.json()['builds']

        # ! Everything is correct, builds are finished, that is why empty tuple is returned
        return tuple(
            self.parse_build(build) for build in builds
            if build['created_by']['login'] == self.author
                and (build['state'] == 'started' or build['state'] == 'created')
        )

    def get_finished_builds(self, initial_builds, running_builds):
        """Return finished builds by comparing current running builds with initial builds.

        Args:
            initial_builds: sequence of initial active builds.
            running_builds: sequence of currently active builds.

        Returns:
            tuple: sequence of finished builds.
        """
        # Too expensive comparison, use smth like shallow comparison
        return tuple(build for build in initial_builds if build not in running_builds)

    def parse_build(self, build):
        # ? use id-build info structure for faster comparison (by id)
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

    def get_failed_job(self, jobs):
        # ? Or just get_failed_job_id
        for job in jobs['jobs']:
            if job['state'] == 'failed':
                return job

    def request_factory(self, path):
        """Factory method for making requests to Travis API.

        Arguments:
            path {[type]} -- [description]
        """
        return requests.get(
            f'https://api.travis-ci.com/{path}',
            headers={
                'Travis-API-Version': '3',
                'User-Agent': 'API Explorer',
                'Authorization': f'token {self.token}'
            }
        )
