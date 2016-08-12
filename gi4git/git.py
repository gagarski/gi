import os
from itertools import *

class Magic:
    HELP_A = "help -a"
    GET_ALIASES = "config --get-regexp --name-only alias"
    CMD_HELP = """man git-{} | col -b"""
    SYNOPSIS = "SYNOPSIS"

def get_git_commands(git="git"):
    """
    Returns a list of available git commands from "git help -a"
    :param git: git executable name
    :return: list of available git commands
    """
    # TODO Is there a more convenient way to get all git commands?
    # TODO Finding git-core directory and traversing path for "git-*" files is not convenient.
    with os.popen("{} {}".format(git, Magic.HELP_A)) as git_help:
        lines_with_commands = (line for line in dropwhile(lambda str: str.strip(), git_help) if
                               line.startswith(" ") and len(line.strip()) != 0)
        commands = list(set(chain.from_iterable(str(line).split() for line in lines_with_commands)))
        return commands


def get_git_aliases(git="git"):
    """
    Returns a list of available git aliases from "git config"
    :param git: git executable name
    :return: list of available git aliases
    """
    with os.popen("{} {}".format(git, Magic.GET_ALIASES)) as git_conf:
        return list(set(str(line.strip()).split(".", 2)[1] for line in git_conf))


def get_git_subcommands(command):
    with os.popen(Magic.CMD_HELP.format(command)) as man:
        man_i = dropwhile(lambda str: not str.strip().startswith(Magic.SYNOPSIS), man)
        try:
            next(man_i)
        except StopIteration:
            return []
        synopsis = takewhile(lambda line: line.strip().startswith("git {}".format(command)), man_i)

        def subcommands_gen():
            for line in synopsis:
                words = line.strip().split()
                if len(words) > 2:
                    subc = [word for word in words[2:] if len(word) != 0 and word[0].isalpha()]
                    if len(subc) != 0:
                        yield subc[0]

        return list(set(subcommands_gen()))

