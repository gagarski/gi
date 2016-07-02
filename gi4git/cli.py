import shlex
from itertools import count

import sys


class GiCli:
    """
    gi command line processor
    """

    # gi CLI options
    BASH_COMPLETION_HELPER = "--gi-bash-completion-helper-with-comp-cword"
    DO_NOT_PROCESS_DASHES = "--gi-do-not-process-dashes"

    # Saving gi options to remove them while generating git command ine options
    KNOWN_OPTS = (DO_NOT_PROCESS_DASHES, )
    KNOWN_KWARGS = (BASH_COMPLETION_HELPER, )
    # These options can be present before a command and their argument can resemble a command
    # E.g. in "gi -C stat pul" "pul" is a command, not "stat". "stat" is a directory.
    GIT_GLOBAL_OPTS_WITH_ARG = ("-C", "-c")

    def __init__(self, argv):
        """
        Constructor
        :param argv: command line arguments
        """
        if len(argv) < 1:
            raise ValueError("argv should contain at least an executable name")
        self.__me = argv[0]
        self.__command = None
        self.__command_pos = None
        self.__process_dashes = True
        self.__bash_completion_helper = False
        self.__bash_completion_cword = None
        self.__bash_completion_cword_empty = False

        skip_next = False

        for i, arg in zip(count(1), argv[1:]):
            if not skip_next and not arg.startswith("-") and self.__command is None:
                self.__command_pos = i
                self.__command = arg
                skip_next = False
            elif arg in self.GIT_GLOBAL_OPTS_WITH_ARG:
                skip_next = True
            elif arg == self.DO_NOT_PROCESS_DASHES:
                self.__process_dashes = False
                skip_next = False
            elif len(arg.split("=")) == 2 and arg.split("=")[0] == self.BASH_COMPLETION_HELPER:
                try:
                    self.__bash_completion_helper = True
                    bash_completion_cword_str, bash_completion_empty_str = arg.split("=")[1].split(",")
                    self.__bash_completion_cword = int(bash_completion_cword_str)
                    self.__bash_completion_cword_empty = bash_completion_empty_str == "True"
                except ValueError:
                    raise ValueError("Bad value for keyword arg {}".format(self.BASH_COMPLETION_HELPER))
                skip_next = False
            else:
                skip_next = False

    def is_bash_completion_helper(self):
        """
        Should we print data for bash completion and exit?
        :return:
        """
        return self.__bash_completion_helper

    def get_bash_completion_cword(self):
        """
        Returns passed cword argument for bash completion
        :return:
        """
        return self.__bash_completion_cword

    def is_bash_completion_cword_empty(self):
        """
        Is bash completion cword empty
        :return:
        """
        return self.__bash_completion_cword_empty

    def is_process_dashes(self):
        """
        Should we perform special processing for dashes in command name?
        :return:
        """
        return self.__process_dashes

    def get_me(self):
        """
        Returns executable name
        :return: executable name
        """
        return self.__me

    def get_command(self):
        """
        Returns a command abbreviation found in CLI arguments
        :return: command abbreviation found in CLI arguments
        """
        return self.__command

    def get_command_pos(self):
        """
        Returns the position of a command abbreviation found in CLI arguments
        :return: position of aabbreviation found in CLI arguments
        :return:
        """
        return self.__command_pos


class CliCleaner:
    """
    Class that cleans up CLI to pass to git
    """

    def __init__(self, argv, git="git"):
        """
        Constructor
        :param argv: command line
        :param git: git executable name
        """
        if len(argv) < 1:
            raise ValueError("argv should contain at least an executable name")

        self.__cleaned_argv = [git]
        self.__arg_removed = [False]
        self.__new_arg_pos = [0]

        current_offset = 0

        for i, arg in zip(count(1), argv[1:]):
            self.__new_arg_pos.append(i + current_offset)

            if arg in GiCli.KNOWN_OPTS:
                self.__arg_removed.append(True)
                current_offset -= 1
            elif len(arg.split("=")) == 2 and arg.split("=")[0] in GiCli.KNOWN_KWARGS:
                self.__arg_removed.append(True)
                current_offset -= 1
            else:
                self.__arg_removed.append(False)
                self.__cleaned_argv.append(arg)

    def is_arg_removed(self, i):
        """
        Was arg #i from the dirty command line removed during clean up?
        :param i: argument index
        :return: True if was, False otherwise
        """
        if i < len(self.__arg_removed):
            return self.__arg_removed[i]
        else:
            return False

    def get_new_arg_pos(self, i):
        """
        Get position for arg #i from dirty the command line in the cleaned up command line
        :param i: arg index
        :return: new argument position
        """
        sz = len(self.__arg_removed)
        if i < sz:
            return self.__new_arg_pos[i]
        else:
            return self.__new_arg_pos[sz - 1] + 1 + (i - sz)

    def get_cleaned_up_args(self):
        """
        Returns cleaned up list of arguments. Eache argument is shell-escaped
        :return: cleaned up list of arguments.
        """
        return [shlex.quote(arg) for arg in self.__cleaned_argv]


def get_args_with_replaced_command(cli, cli_cleaner, command):
    """
    Returns args with command replaced by the 'command' argument
    :param cli: GiCli object
    :param cli_cleaner: CliCleaner object
    :param command: new command
    :return: args with command replaced by the 'command' argument
    """

    args = cli_cleaner.get_cleaned_up_args()
    args[cli_cleaner.get_new_arg_pos(cli.get_command_pos())] = command
    return args


def print_bash_completion_output(cli, cli_cleaner, cword, cword_empty, new_command=None):
    """
    Prints output that bash completion script excepts to read.
    If 'new_command' is not None, then command in argv replaced with new_command
    :param cli: GiCli object
    :param cli_cleaner: CliCleaner object
    :param cword: COMP_CWORD bash variable value
    :param new_command: found git command, None if none
    :return:
    """
    print(cli_cleaner.is_arg_removed(cword) and not cword_empty)
    print(cli_cleaner.get_new_arg_pos(cword))
    if new_command is not None:
        args = get_args_with_replaced_command(cli, cli_cleaner, new_command)
    else:
        args = cli_cleaner.get_cleaned_up_args()

    for i, arg in enumerate(args):
        if cword == i and cword_empty:
            print()
        print(arg)

    if cword == len(args) and cword_empty:
        print()


def get_command_line(cli, cli_cleaner, new_command=None):
    """
    Returns GIT command line.
    If 'new_command' is not None, then command in argv replaced with new_command
    :param cli: GiCli object
    :param cli_cleaner: CliCleaner object
    :param new_command: found git command, None if none
    :return: git command line
    """
    if new_command is not None:
        args = get_args_with_replaced_command(cli, cli_cleaner, new_command)
    else:
        args = cli_cleaner.get_cleaned_up_args()

    return " ".join(args)
