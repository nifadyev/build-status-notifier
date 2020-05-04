"""Main module for running bot with one of available pair of CI system and notifier."""

import json
from typing import Type, Dict
from src.ci_systems.travis import Travis
from src.notifiers.slack import Slack


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


def run_bot(ci_system: Type[Travis], notifier: Type[Slack]) -> None:
    """Start listening for incoming messages.

    Args:
        ci_system: Drone, Travis or Jenkins class.
        notifier: Slack class.
    """
    config = load_config('config.json')
    # config = load_config(CONFIG_PATH)
    # ? How to get required tokens based on chosen ci_system and notifier
    chosen_notifier = notifier(config['slack'], ci_system(config['travis']))
    # chosen_notifier = notifier(config['slack']['token'], ci_system(config))
    chosen_notifier.start()


if __name__ == "__main__":
    print('Bot is running\n')
    run_bot(Travis, Slack)
    print('Bot has been terminated')
