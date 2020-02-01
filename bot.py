"""Main module for running bot with one of available pair of CI system and notifier."""

import json
from typing import Union, Type, Dict
from src.ci_systems.drone import Drone
from src.notifiers.slack import Slack


# ! Tasks
# TODO: add base abstract class for all ci_systems
# TODO: Check with empty path in load_config
# TODO: Use logging module


CONFIG_PATH = '/home/nifadyev/code/build-status-notifier/config.json'


def load_config(path: str) -> Dict[str, str]:
    """Load JSON configuration file with required user specific data.

    File should contain tokens for used CI system APIs and channel and user ids for notifier.

    Args:
        path: full path to JSON configuration file.

    Returns:
        dict: configuration.
    """
    with open(path) as config:
        return json.load(config)


def run_bot(ci_system: Union[Type[Drone], ], notifier: Union[Type[Slack], ]) -> None:
    """Start listening for incoming messages.

    Args:
        ci_system: Drone, Travis or Jenkins class.
        notifier: Slack class.
    """
    config = load_config(CONFIG_PATH)
    # ? How to get required tokens based on chosen ci_system and notifier
    chosen_notifier = notifier(config['slackbot_token'], ci_system())
    chosen_notifier.start()


if __name__ == "__main__":
    # ? Decorator for wrapping up run_bot with logging
    print('Bot is running\n')
    run_bot(Drone, Slack)
    print('Bot has been terminated')
