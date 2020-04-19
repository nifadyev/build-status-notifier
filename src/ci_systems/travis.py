"""Module for dealing with Travis CI API."""

import json
import time
# from typing import Dict, Any, Union, List, Tuple

import requests
from slack.web.client import WebClient

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
        # ? use global frequency for all CI systems
        self.frequency = config['drone']['request_frequency']
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
            # TODO: Pass repository when multi repo support is implemented
            self.monitor_active_builds(web_client)
        elif command == 'restart':
            # * suggest to restart if error status, not failed
            pass
        elif command == 'kill':
            # * suggest to kill if commit contains WIP or work in progress
            pass
        else:
            print('Unsupported command')

    def monitor_active_builds(self, web_client):
        """Check build statuses for specified author and repository.

        Args:
            web_client: Slack web client.
            repository: Supported repository name.
            author: author name in Drone.
        """
        # ! Steps:
        # ! 1. Get list of initial builds
        # ! 2. While there are running builds run endless cycle
        # ! 2.1 Get list of running builds
        # ! 2.2 Check if anything has changed since initial builds
        # ! 2.2.1 If no, sleep
        # ! 2.2.1 If yes, get list of finished builds
        # ! 2.3 Process finished builds
        # ! 2.3.1 Compose message for each build and send it to Slack
        # ! 2.4 If no active build left, break
        # ! 2.5 Sleep
        # ! initial builds
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

            # TODO: try to make only 1 request and filter finished builds
            for build in self.get_finished_builds(monitored_builds, running_builds):
                finished_build = build
                # Do not send message if build status has changed from `pending` to `running`
                # TODO: check this values for Travis and move this to common const
                if finished_build['state'] in ('pending', 'running'):
                    continue

                message = Slack.make_message(finished_build)
                if not Slack.send_message(web_client, self.channel, message):
                    print(f'Message has not been sent to {self.channel}')

            monitored_builds = running_builds

            if not monitored_builds:
                # ! MAIN
                print('Finishing monitoring')
                # TODO: make a decorator to check if message has been sent successfully
                if not Slack.send_message(web_client, self.channel, 'Running builds are finished'):
                    print(f'Message has not been sent to {self.channel}')
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
        request = requests.get(
            f'https://api.travis-ci.com/repo/{self.repository_id}/builds',
            headers={
                'Travis-API-Version': '3',
                'User-Agent': 'API Explorer',
                'Authorization': f'token {self.token}'
            }
        )

        builds = json.loads(request.content)['builds']

        # TODO: calculate build duration, does not pass started_at and finished_at
        # TODO: move to sep func
        return tuple(
            {
                'id': build['id'],
                'event': build['event_type'],
                'status': build['state'],
                # ? is branch used somewhere
                # 'branch': build['branch'],
                'message': build['commit']['message'],
                'duration': build['duration'],
                'started_at': build['started_at'],
                'finished_at': build['finished_at'],
                'url': build['commit']['compare_url']
            }
            for build in builds
            # TODO: move build status check to sep func
            if build['created_by']['login'] == self.author\
                and (build['state'] == 'pending' or build['state'] == 'running')
        )

    # ! Common module
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

    def send_example_request(self):
        # ! Working

        request = requests.get(
            # * get info about all repos
            # 'https://api.travis-ci.com/repos',
            f'https://api.travis-ci.com/repo/{self.repository_id}/builds',
            headers={
                'Travis-API-Version': '3',
                'User-Agent': 'API Explorer',
                'Authorization': f'token {self.token}'
            }
        )

        print(request.status_code)
        with open('running_builds.json', 'w+', encoding='utf-8') as output:
            json.dump(request.json(), output, indent=4)

# ! For now write working module for Travis and then got to refactoring and creating common base module
# ? Use requests templates (with headers) to move get_running_builds to common base module
