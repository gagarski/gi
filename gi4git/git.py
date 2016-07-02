import os
from itertools import *

__git_help_a = "help -a"
__git_get_aliases = "config --get-regexp --name-only alias"


def get_git_commands(git="git"):
    """
    Returns a list of available git commands from "git help -a"
    :param git: git executable name
    :return: list of available git commands
    """
    # TODO Is there a more convenient way to get all git commands?
    # TODO Finding git-core directory and traversing path for "git-*" files is not convenient.
    with os.popen("{} {}".format(git, __git_help_a)) as git_help:
        lines_with_commands = (line for line in dropwhile(lambda str: str.strip(), git_help) if
                               line.startswith(" ") and len(line.strip()) != 0)
        commands = list(chain.from_iterable(str(line).split() for line in lines_with_commands))
        return commands


def get_git_aliases(git="git"):
    """
    Returns a list of available git aliases from "git config"
    :param git: git executable name
    :return: list of available git aliases
    """
    with os.popen("{} {}".format(git, __git_get_aliases)) as git_conf:
        return [str(line.strip()).split(".", 2)[1] for line in git_conf]
