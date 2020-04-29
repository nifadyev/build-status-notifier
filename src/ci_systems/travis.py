"""Module for dealing with Travis CI API."""

import time
# from typing import Dict, Any, Union, List, Tuple

import requests

from src.notifiers.slack import Slack


class Travis():
    """Class for sending requests via Travis API and parsing their response."""

    def __init__(self, config) -> None:
        """Initialize class instance.

        Args:
            config: part of JSON config file related to Drone CI API.

        Attributes:
            token: key for communicating with Drone CI API.
            author: author name in Drone.
            channel: bot direct message ID.
            repositories: list of monitored repositories.
            root_url: root for full repository url.
            frequency: interval in seconds between consecutive requests to API.
        """
        self.token = config['travis']['token']
        self.author = config['travis']['author']['login']
        self.channel = config['slack']['bot_direct_messages_id']
        self.frequency = config['travis']['request_frequency']
        self.repository_id = config['travis']['repositories'][0]['id']

    def execute_command(self, web_client, command, args=None):
        """Execute requested command with optional arguments.

        Args:
            web_client: Slack web client.
            command: Valid keyword.
            args: Optional arguments for some commands.

        Returns:
            int: Execution status
        """
        if command == 'monitor':
            print(f'Executing command {command} {args or ""}')
            self.monitor_active_builds(web_client)
        else:
            print('Unsupported command')

    def monitor_active_builds(self, web_client):
        """Check build statuses for specified author and repository.

        Args:
            web_client: Slack web client.
            repository: Supported repository name.
            author: author name in Drone.
        """
        monitored_builds = self.get_running_builds()
        # Initial check for author's active builds
        if not monitored_builds:
            print('Running builds are not found')
            return

        # builds with what names are monitored
        # what stages are passed, how many are being ran ATM
        print(f'{len(monitored_builds)} builds are monitored')

        # Run endless loop till all build are finished
        while True:
            running_builds = self.get_running_builds()
            # ? It is necessary per each iteration
            print(f'{len(running_builds)} builds are are still in progress')

            # Initial builds are still being ran
            # ? Probably too expensive comparison
            if running_builds == monitored_builds:
                time.sleep(self.frequency)
                continue

            for build in self.get_finished_builds(monitored_builds, running_builds):
                request = requests.get(
                    f'https://api.travis-ci.com/build/{build["id"]}',
                    headers={
                        'Travis-API-Version': '3',
                        'User-Agent': 'API Explorer',
                        'Authorization': f'token {self.token}'
                    }
                )
                finished_build = self.parse_build(build=request.json())

                # Do not send message if build status has changed from `pending` to `running`
                # TODO: check this values for Travis and move this to common const
                if finished_build['status'] in ('started', 'created', 'pending', 'running'):
                    continue

                if finished_build['status'] == 'failed':
                    print(finished_build)
                    jobs_request = requests.get(
                        f'https://api.travis-ci.com/build/{finished_build["id"]}/jobs',
                        headers={
                            'Travis-API-Version': '3',
                            'User-Agent': 'API Explorer',
                            'Authorization': f'token {self.token}'
                        }
                    )
                    # import pdb; pdb.set_trace()
                    print(jobs_request.json())
                    failed_job = self.get_failed_job(jobs_request.json())

                    # ! Does not suitable for multiple failed jobs
                    jobs_log_request = requests.get(
                        f'https://api.travis-ci.com/job/{failed_job["id"]}/log',
                        headers={
                            'Travis-API-Version': '3',
                            'User-Agent': 'API Explorer',
                            'Authorization': f'token {self.token}'
                        }
                    )
                    jobs_log = jobs_log_request.json()['content']
                    # Last 3 strings are useless, display -8:-3 strings
                    # * Or better to set how many strings to show in config
                    # * For example, if there are lots of tests, just print info about how many of them failed
                    # * But, of course, do it later
                    error_strings = jobs_log.splitlines()[-8:-3]
                    message = Slack.make_failure_message(
                        finished_build, error_strings, failed_job['id'])
                else:
                    message = Slack.make_message(finished_build)

                if not Slack.send_message(web_client, self.channel, message):
                    print(f'Message has not been sent to {self.channel}')

            monitored_builds = running_builds

            if not monitored_builds:
                print('Finishing monitoring')
                if not Slack.send_message(web_client, self.channel, 'Running builds are finished'):
                    print(f'Message has not been sent to {self.channel}')
                # This  break does not end endless loop, use some flag to end it (or never end it)
                break

            time.sleep(self.frequency)

    def get_running_builds(self):
        """Return list of active builds for specified repository and author.

        Args:
            repository: Supported repository name.

        Returns:
            tuple: sequence of active author's builds.
        """
        # Get list of all builds
        # TODO: create factory or wrapper for request, or make headers constant
        request = requests.get(
            f'https://api.travis-ci.com/repo/{self.repository_id}/builds',
            headers={
                'Travis-API-Version': '3',
                'User-Agent': 'API Explorer',
                'Authorization': f'token {self.token}'
            }
        )

        builds = request.json()['builds']

        # TODO: calculate build duration, does not pass started_at and finished_at
        # ! Everything is correct, builds are finished, that is why empty tuple is returned
        return tuple(
            self.parse_build(build) for build in builds
            if build['created_by']['login'] == self.author\
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
