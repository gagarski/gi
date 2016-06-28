import shlex
from itertools import count


class GiCli:
    """
    gi command line processor
    """

    # gi CLI options
    PRINT_ME = "--gi-print-me"
    DO_NOT_PROCESS_DASHES = "--gi-do-not-process-dashes"

    # Saving gi options to remove them while generating git command ine options
    KNOWN_ARGS = (PRINT_ME, DO_NOT_PROCESS_DASHES)

    # These options can be present before a command and their argument can resemble a command
    # E.g. in "gi -C stat pul" "pul" is a command, not "stat". "stat" is a directory.
    GIT_GLOBAL_OPTS_WITH_ARG = ("-C", "-c")

    def __find_command(self):
        """
        Finds command abbreviation in gi command line arguments
        :return tuple of the found abbreviation position and the abbreviation itself
        """
        skip_next = False

        for i, arg in zip(count(1), self.__argv[1:]):
            if not skip_next and not arg.startswith("-"):
                return i, arg
            elif arg in self.GIT_GLOBAL_OPTS_WITH_ARG:
                skip_next = True
            else:
                skip_next = False

        return None, None

    def __init__(self, argv):
        """
        Constructor
        :param argv: command line arguments
        """
        if len(argv) < 1:
            raise ValueError("argv should contain at least an executable name")

        self.__argv = list(argv)
        (self.__command_pos, self.__command) = self.__find_command()

    def is_print_me(self):
        """
        Should we pring git command line and exit?
        :return:
        """
        return self.PRINT_ME in self.__argv

    def is_process_dashes(self):
        """
        Should we perform special processing for dashes in command name?
        :return:
        """
        return self.DO_NOT_PROCESS_DASHES not in self.__argv

    def get_me(self):
        """
        Returns executable name
        :return: executable name
        """
        return self.__argv[0]

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

    def make_git_cli(self, replacement=None, git="git"):
        """
        Generates GIT command line to execute or print
        :param replacement: git command to replace found abbreviation
        :param git: git executable name
        :return: GIT command line to execute or print
        """
        new_argv = list(self.__argv)
        new_argv[0] = git
        if self.__command_pos is not None and replacement is not None:
            new_argv[self.__command_pos] = replacement
        return " ".join([shlex.quote(arg) for arg in (filter(lambda arg: arg not in self.KNOWN_ARGS, new_argv))])

