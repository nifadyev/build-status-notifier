"""Main module for running bot with one of available pair of CI system and notifier."""

import json
from typing import Union, Type, Dict
from src.ci_systems.drone import Drone
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


def run_bot(ci_system: Union[Type[Drone], Type[Travis]], notifier: Union[Type[Slack], ]) -> None:
    """Start listening for incoming messages.

    Args:
        ci_system: Drone, Travis or Jenkins class.
        notifier: Slack class.
    """
    config = load_config('config.json')
    # config = load_config(CONFIG_PATH)
    # ? How to get required tokens based on chosen ci_system and notifier
    chosen_notifier = notifier(config['slack']['token'], ci_system(config))
    # chosen_notifier = notifier(config['slack']['token'], ci_system(config['drone']))
    # chosen_notifier = notifier(config['slackbot_token'], ci_system())
    # ! RTMClient has method stop
    chosen_notifier.start()


if __name__ == "__main__":
    # ? Decorator for wrapping up run_bot with logging
    print('Bot is running\n')
    # ! Slack RTMClient ATM cannot be stopped properly on Windows (not implemented)
    run_bot(Travis, Slack)
    # run_bot(Drone, Slack)
    print('Bot has been terminated')
