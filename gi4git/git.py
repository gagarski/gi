import os
from itertools import *
import re


class Magic:
    HELP_A = "help -a --no-verbose"
    GET_ALIASES = "config --get-regexp --name-only alias"
    CMD_HELP = """help {} | col -b"""
    SYNOPSIS = "SYNOPSIS"


def get_git_commands(git="git"):
    """
    Returns a list of available git commands from "git help -a --no-verbose"
    :param git: git executable name
    :return: list of available git commands
    """
    # TODO Is there a more convenient way to get all git commands?
    # TODO Finding git-core directory and traversing path for "git-*" files is not convenient.
    with os.popen("{} {}".format(git, Magic.HELP_A)) as git_help:
        lines_with_commands = (line for line in dropwhile(lambda line: line.strip(), git_help) if
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


__subc_re = re.compile(r"^[A-Za-z][A-Za-z0-9\-]*$")


def get_git_subcommands(command, git="git"):
    with os.popen("{} {}".format(git, Magic.CMD_HELP.format(command))) as man:
        man_i = dropwhile(lambda line: not line.strip().startswith(Magic.SYNOPSIS), man)
        try:
            next(man_i)
        except StopIteration:
            return []
        synopsis = takewhile(lambda line: len(line.strip()) != 0, man_i)

        def synopsis_gen():
            cur_cmd = None
            for line in synopsis:
                stripped = line.strip()
                if stripped.startswith("{} {}".format(git, command)):
                    if cur_cmd is not None:
                        yield cur_cmd
                    cur_cmd = stripped
                elif cur_cmd is not None:
                    cur_cmd += " "
                    cur_cmd += stripped
                else:
                    cur_cmd = None
                    continue

            if cur_cmd is not None:
                yield cur_cmd

        def subcommands_gen():
            for line in synopsis_gen():
                words = line.strip().split()
                if len(words) > 2:
                    subc = [word for word in words[2:] if len(word) != 0 and __subc_re.match(word)]
                    if len(subc) != 0:
                        yield subc[0]

        return list(set(subcommands_gen()))
