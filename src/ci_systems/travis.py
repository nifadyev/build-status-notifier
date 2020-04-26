"""Module for dealing with Travis CI API."""

import json
import time
# from typing import Dict, Any, Union, List, Tuple

import requests
from slack.web.client import WebClient

from src.notifiers.slack import Slack

# ! If build failed, return link to failed job (ex. https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/320766424)
# ! And last strings from log
# TODO: get last strings from JSON logs
# ! 2 requests from get_running_builds(), 1 for getting jobs, 1 for log

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
            self.monitor_active_builds(web_client)
        # elif command == 'restart':
        #     # * suggest to restart if error status, not failed
        #     pass
        # elif command == 'kill':
        #     # * suggest to kill if commit contains WIP or work in progress
        #     pass
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
            # import pdb; pdb.set_trace()
            running_builds = self.get_running_builds()
            # ? It is necessary per each iteration
            print(f'{len(running_builds)} builds are are still in progress')

            # Initial builds are still being ran
            # ? Probably too expensive comparison
            if running_builds == monitored_builds:
                time.sleep(self.frequency)
                continue
            status = []
            for build in self.get_finished_builds(monitored_builds, running_builds):
                request = requests.get(
                    f'https://api.travis-ci.com/repo/build/{build["id"]}',
                    headers={
                        'Travis-API-Version': '3',
                        'User-Agent': 'API Explorer',
                        'Authorization': f'token {self.token}'
                    }
                )
                finished_build = self.parse_build(request)
                # Do not send message if build status has changed from `pending` to `running`
                # TODO: check this values for Travis and move this to common const
                if finished_build['status'] in ('pending', 'running'):
                # if finished_build['state'] in ('pending', 'running'):
                    status.append(finished_build['status'])
                    continue

                status.append(finished_build['status'])
                message = Slack.make_message(finished_build)
                if not Slack.send_message(web_client, self.channel, message):
                    print(f'Message has not been sent to {self.channel}')

            monitored_builds = running_builds

            if not monitored_builds:
                print('Finishing monitoring')
                if not Slack.send_message(web_client, self.channel, f'{status} Running builds are finished'):
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

        # ? requests.json()
        builds = request.json()['builds']
        # import pdb; pdb.set_trace()
        # print(builds == json.loads(request.content)['builds'])
        # builds = json.loads(request.content)['builds']

        # TODO: calculate build duration, does not pass started_at and finished_at
        # ! Everything is correct, builds are finished, that is why empty tuple is returned
        return tuple(
            {
                'id': build['id'],
                'event': build['event_type'],
                'status': build['state'],
                # ? is branch used somewhere
                'branch': build['branch'],
                'message': build['commit']['message'],
                'duration': build['duration'],
                'started_at': build['started_at'],
                'finished_at': build['finished_at'],
                'url': build['commit']['compare_url']
            }
            for build in builds
            if build['created_by']['login'] == self.author\
                and (build['state'] == 'pending' or build['state'] == 'running')
                # and (build['state'] == 'pending' or build['state'] == 'running')
        )

    # ! Broken for travis
    # Return build with 'running' status
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

        # return tuple(
        #     build for build in running_builds
        #     if build['status'] not in ('pending', 'running') and build in initial_builds
        # )

    def parse_build(self, request):
        build = request.json()

        return {
            'id': build['id'],
            'event': build['event_type'],
            'status': build['state'],
            # ? is branch used somewhere
            # * Used in slack.py (compare with master)
            'branch': build['branch'],
            'message': build['commit']['message'],
            'duration': build['duration'],
            'started_at': build['started_at'],
            'finished_at': build['finished_at'],
            'url': build['commit']['compare_url']
        }
    def send_example_request(self):
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
