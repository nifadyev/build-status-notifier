"""Main module for running bot with one of available pair of CI system and notifier."""

import json
from typing import Type, Dict

from src.ci_systems.travis import Travis
from src.notifiers.slack import Slack


def load_config(path: str) -> Dict[str, Any]:
    """Load JSON configuration file with required user specific data.

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
    chosen_notifier = notifier(config['slack'], ci_system(config['travis']))

    chosen_notifier.start()


if __name__ == "__main__":
    print('Bot is running\n')
    run_bot(Travis, Slack)
    print('Bot has been terminated')
