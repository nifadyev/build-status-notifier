"""Module for dealing with Drone CI API."""

import json
import time
from typing import Dict, Any, Union, List, Tuple

import requests
from slack.web.client import WebClient

from src.notifiers.slack import Slack


class Drone():
    """Class for sending requests via Drone API and parsing their response."""

    def __init__(self, config: Dict[str, Dict[str, Union[str, int]]]) -> None:
    # def __init__(self, config: Dict[str, Union[str, int]]) -> None:
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
        self.token = config['drone']['token']
        self.author = config['drone']['author']
        self.channel = config['slack']['bot_direct_messages_id']
        self.repositories = config['drone']['repositories']
        self.root_url = config['drone']['root_url']
        self.frequency = config['drone']['request_frequency']

    def execute_command(
            self, web_client: WebClient, command: str, args: List[Union[str, int]] = None) -> None:
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
            self.monitor_active_builds(web_client, args, author=self.author)
            # return
        else:
            print('Unsupported command')
            # return smth

    def monitor_active_builds(
            self,
            web_client: WebClient,
            # web_client: WebClient = None,
            repository: str = 'integrations',
            author: str = 'all'
    ) -> None:
        """Check build statuses for specified author and repository.

        TODO
        Write somewhere list of active builds (S3 or DynamoDB)
        Read this every N seconds, delete finished build from this list
        Repeat till list is empty

        Args:
            web_client: Slack web client.
            repository: Supported repository name.
            author: author name in Drone.
        """
        monitored_builds = self.get_running_builds(repository)

        # Initial check for author's active builds
        if not monitored_builds:
            print('Running builds not found')
            return

        # builds with what names are monitored
        # what stages are passed, how many are being ran ATM
        print(f'{len(monitored_builds)} builds are monitored')

        # Run endless loop till all build are finished
        while True:
            running_builds = self.get_running_builds(repository)
            # ? It is necessary per each iteration
            print(f'{len(running_builds)} builds are are still in progress')

            # Initial builds are still being ran
            # ? Probably too expensive comparison
            if running_builds == monitored_builds:
                time.sleep(self.frequency)
                continue

            # TODO: try to make only 1 request and filter finished builds
            for build in self.get_finished_builds(monitored_builds, running_builds):
                # Use Session to optimize requests response time
                request = requests.get(
                    f'{self.root_url}{repository}/builds/{build["number"]}',
                    headers={'Authorization': f'Bearer {self.token}'}
                )
                # * Use for test only
                finished_build = request.content
                # finished_build = json.loads(request.content)
                # Do not send message if build status has changed from `pending` to `running`
                if finished_build['status'] in ('pending', 'running'):
                    continue

                message = Slack.make_message(finished_build)
                if not Slack.send_message(web_client, self.channel, message):
                    print(f'Message has not been sent to {self.channel}')

            monitored_builds = running_builds

            if not monitored_builds:
                print('Finishing monitoring')
                if not Slack.send_message(web_client, self.channel, 'Running builds are finished'):
                    print(f'Message has not been sent to {self.channel}')
                break

            time.sleep(self.frequency)

    def get_running_builds(self, repository: str) -> Tuple[Dict[str, Union[str, int]]]:
        """Return list of active builds for specified repository and author.

        Args:
            repository: Supported repository name.

        Returns:
            tuple: sequence of active author's builds.
        """
        # Get list of all builds
        request = requests.get(
            f'{self.root_url}{repository}/builds',
            headers={'Authorization': f'Bearer {self.token}'}
        )
        # * Use for test only
        builds = request.content
        # builds = json.loads(request.content)

        # TODO: calculate build duration, does not pass started_at and finished_at
        return tuple(
            {
                # ? rename to build id if it is id
                'number': build['number'],
                'event': build['event'],
                'status': build['status'],
                # ? is branch used somewhere
                'branch': build['branch'],
                'commit message': build['message'],
                'started_at': build['started_at'],
                'finished_at': build['finished_at'],
                'url': build['link_url']
            }
            for build in builds
            if build['author'] == self.author\
                and (build['status'] == 'pending' or build['status'] == 'running')
        )

    def get_finished_builds(
            self,
            initial_builds: Tuple[Dict[str, Union[str, int]]],
            running_builds: Tuple[Dict[str, Union[str, int]]]
    ) -> Tuple[Dict[str, Union[str, int]]]:
        """Return finished builds by comparing current running builds with initial builds.

        Args:
            initial_builds: sequence of initial active builds.
            running_builds: sequence of currently active builds.

        Returns:
            tuple: sequence of finished builds.
        """
        return tuple(build for build in initial_builds if build not in running_builds)
