"""Module for dealing with Drone CI API."""

import json
import time
import requests
from src.notifiers.slack import Slack

# TODO: add base abstract class for all ci_systems
FREQUENCY = 30  # Seconds between request to Drone CI API


class Drone():
    def __init__(self, config):
        # TODO: pass only Drone part of config
        self.token = config['drone']['token']
        self.author = config['drone']['author']
        self.channel = config['slack']['bot_direct_messages_id']
        self.repositories = config['drone']['repositories']
        self.root_url = config['drone']['root_url']
        self.frequency = config['drone']['request_frequency']

    def execute_command(self, web_client, command, args=None):
        """Execute requested command with optional arguments.

        param: web_client -- Slack client for interaction.
        param: command -- valid keyword.
        param: args -- optional arguments for some commands.

        returns: execution status
        """
        if command == 'monitor':
            self.monitor_active_builds(web_client, args, author=self.author)
        else:
            print('Unsupported command')

    # Write somewhere list of active builds (S3 or DynamoDB)
    # Read this every N seconds, delete finished build from this list
    # Repeat till list is empty
    def monitor_active_builds(self, web_client=None, repository='integrations', author='all'):
        monitored_builds = self.get_running_builds(repository, author=self.author, flag=False)
        # print(monitored_builds)
        if not monitored_builds:
            print('Running builds not found')
            return
        # TODO: make information about progress more specific
        # builds with what names are monitored
        # what stages are passed, how many are being ran ATM
        print(f'{len(monitored_builds)} builds are monitored')

        # Run endless loop till all build are finished
        while True:
            running_builds = self.get_running_builds(repository, author=self.author, flag=True)
            print(f'{len(running_builds)} builds are are still in progress')
            # Initial builds are still being ran
            if running_builds == monitored_builds:
                time.sleep(self.request_frequency)
                continue

            # TODO: try to make only 1 request and filter finished builds
            for build in self.get_finished_builds(monitored_builds, running_builds):
                # Use Session to optimize requests response time
                # request = requests.get(
                #     f'{self.root_url}{repository}/builds/{build["number"]}',
                #     headers={'Authorization': f'Bearer {DRONE_TOKEN}'}
                # )
                # finished_build = json.loads(request.content)
                with open('/home/nifadyev/storage/Code/Work/drone-ci-bot/finished_build.json') as bld:
                    finished_build = json.loads(bld.read())
                # Do not send message if build status has changed from `pending` to `running`
                if finished_build['status'] in ('pending', 'running'):
                    continue
                message = Slack.make_message(finished_build)

                # ! SLACK Part
                if web_client:
                    web_client.chat_postMessage(
                        channel=self.channel,
                        text=message
                    )
                # else:
                #     requests.post(
                #         url='https://slack.com/api/chat.postMessage',
                #         json={"channel": "DP7AHFC13", "text": message},
                #         headers={
                #             "Content-Type": "application/json; charset=utf-8",
                #             "Authorization": f"Bearer {SLACKBOT_TOKEN}"
                #         }
                #     )

            monitored_builds = running_builds

            if not monitored_builds:
                # ! MAINI
                print('Finishing monitoring')
                # ! SLACK Part
                if web_client:
                    web_client.chat_postMessage(
                        channel=self.channel,
                        text='Running builds are finished'
                    )
                    break
                # else:
                #     requests.post(
                #         url='https://slack.com/api/chat.postMessage',
                #         json={"channel": "DP7AHFC13", "text": message},
                #         headers={
                #             "Content-Type": "application/json; charset=utf-8",
                #             "Authorization": f"Bearer {SLACKBOT_TOKEN}"
                #         }
                #     )
                #     break

            time.sleep(self.request_frequency)

    def get_running_builds(self, repository, author='all', flag=False):
    # def get_running_builds(self, repository, author='all'):
        # Get list of all builds
        # request = requests.get(
        #     f'{self.root_url}{repository}/builds',
        #     headers={'Authorization': f'Bearer {DRONE_TOKEN}'}
        # )
        # builds = json.loads(request.content)
        if not flag:
            with open('/home/nifadyev/storage/Code/Work/drone-ci-bot/initial_builds.json') as blds:
                builds = json.loads(blds.read())
        else:
            with open('/home/nifadyev/storage/Code/Work/drone-ci-bot/1_build_is_finished.json') as blds:
                builds = json.loads(blds.read())
        # print(builds)
        # Get active builds
        if author == 'all':
            running_builds = [
                {
                    'number': build['number'],
                    'event': build['event'],
                    'status': build['status'],
                    'branch': build['branch'],
                    'commit message': build['message'],
                    'author': build['author'],
                    'started_at': build['started_at'],
                    'finished_at': build['finished_at'],
                    'url': build['link_url']
                }
                for build in builds
                if (build['status'] == 'pending' or build['status'] == 'running')
            ]
        else:
            running_builds = [
                {
                    'number': build['number'],
                    'event': build['event'],
                    'status': build['status'],
                    'branch': build['branch'],
                    'commit message': build['message'],
                    'started_at': build['started_at'],
                    'finished_at': build['finished_at'],
                    'url': build['link_url']
                }
                for build in builds
                if build['author'] == self.author and (build['status'] == 'pending' or build['status'] == 'running')
            ]

        return running_builds

    def get_finished_builds(self, initial_builds, running_builds):
        """Return finished builds by comparing current running builds with initial builds."""
        finished_builds = []

        for build in initial_builds:
            if build not in running_builds:
                finished_builds.append(build)

        return finished_builds
