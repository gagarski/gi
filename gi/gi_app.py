import sys

import os

from gi.git import get_git_commands, get_git_aliases
from gi.processing import CommandsFinder
from gi.cli import GiCli, CliCleaner, print_bash_completion_output, get_command_line


def gi(argv):
    """
    Executes tool
    :param argv: command line arguments
    :return:
    """
    cli = GiCli(argv)
    trie = CommandsFinder(get_git_commands(), get_git_aliases(), cli.is_process_dashes())
    cli_cleaner = CliCleaner(argv)

    if cli.is_bash_completion_helper() and cli.get_command() is None:
        print_bash_completion_output(cli,
                                     cli_cleaner,
                                     cli.get_bash_completion_cword(),
                                     cli.is_bash_completion_cword_empty())
    elif cli.is_bash_completion_helper():
        possible_commands = trie.possible_commands(cli.get_command())
        if len(possible_commands) == 1:
            print_bash_completion_output(cli, cli_cleaner,
                                         cli.get_bash_completion_cword(),
                                         cli.is_bash_completion_cword_empty(),
                                         possible_commands[0])
        else:
            print_bash_completion_output(cli,
                                         cli_cleaner,
                                         cli.get_bash_completion_cword(),
                                         cli.is_bash_completion_cword_empty())
    elif cli.get_command() is None:
        # Just git with arguments. No commands.
        # E.g. "git --version"
        os.system(get_command_line(cli, cli_cleaner))
    else:
        possible_commands = trie.possible_commands(cli.get_command())
        if len(possible_commands) == 0:
            print("{}: could not find git command starting with '{}'".format(cli.get_me(), cli.get_command()),
                  file=sys.stderr)
        elif len(possible_commands) == 1:
            os.system(get_command_line(cli, cli_cleaner, possible_commands[0]))
        else:
            print("{}: ambiguous git command '{}'".format(cli.get_me(), cli.get_command()), file=sys.stderr)
            print("Possible git commands: ".format(cli.get_me(), cli.get_command()), file=sys.stderr)
            for cmd in possible_commands:
                print("  {}".format(cmd))
