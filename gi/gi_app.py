import sys

import os

from gi.git import get_git_commands, get_git_aliases
from gi.processing import CommandsFinder
from gi.cli import GiCli


def gi(argv):
    """
    Executes tool
    :param argv: command line arguments
    :return:
    """
    cli = GiCli(argv)
    trie = CommandsFinder(get_git_commands(), get_git_aliases(), cli.is_process_dashes())
    if cli.is_print_me() and cli.get_command() is None:
        print(cli.make_git_cli())
    elif cli.is_print_me():
        # This probably can help to delegate bash completion to standard bash completion handler for git
        # but I don't know how it works.
        possible_commands = trie.possible_commands(cli.get_command())
        if len(possible_commands) == 1:
            print(cli.make_git_cli(possible_commands[0]))
        else:
            print(cli.make_git_cli())
    elif cli.get_command() is None:
        # Just git with arguments. No commands.
        # E.g. "git --version"
        os.system(cli.make_git_cli())
    else:
        possible_commands = trie.possible_commands(cli.get_command())
        if len(possible_commands) == 0:
            print("{}: could not find git command starting with '{}'".format(cli.get_me(), cli.get_command()),
                  file=sys.stderr)
        elif len(possible_commands) == 1:
            os.system(cli.make_git_cli(possible_commands[0]))
        else:
            print("{}: ambiguous git command '{}'".format(cli.get_me(), cli.get_command()), file=sys.stderr)
            print("Possible git commands: ".format(cli.get_me(), cli.get_command()), file=sys.stderr)
            for cmd in possible_commands:
                print("  {}".format(cmd))
