import shlex
from enum import Enum

from gi4git.git import get_git_aliases, get_git_commands
from gi4git.git import get_git_subcommands
from gi4git.processing import CommandFinder


class CLIVisitor:
    class State(Enum):
        INIT = 0
        NORMAL = 1
        GLOBAL_OPT_WITH_ARG = 2
        DONE = 3

    # gi CLI options
    BASH_COMPLETION_HELPER = "--gi-bash-completion-helper-with-comp-cword"
    GIT = "--gi-git"
    DO_NOT_PROCESS_DASHES = "--gi-do-not-process-dashes"

    # Saving gi options to remove them while generating git command ine options
    KNOWN_OPTS = (DO_NOT_PROCESS_DASHES, )
    KNOWN_KWARGS = (BASH_COMPLETION_HELPER, GIT)
    # These options can be present before a command and their argument can resemble a command
    # E.g. in "gi -C stat pul" "pul" is a command, not "stat". "stat" is a directory.
    GIT_GLOBAL_OPTS_WITH_ARG = ("-C", "-c")

    def __init__(self, argv):
        self.argv = argv
        self.__state = CLIVisitor.State.INIT
        self.__global_option_with_arg = None

    def visit_me(self, me, index):
        pass

    def visit_global_option_with_arg(self, option, arg, index):
        pass

    def visit_option(self, option, index):
        pass

    def visit_parameter(self, parameter, index):
        pass

    def visit_gi_option(self, option, index):
        pass

    def visit_gi_kwarg(self, key, value, index):
        pass

    def run(self):
        for index, arg in enumerate(self.argv):
            if self.__state == CLIVisitor.State.INIT:
                self.visit_me(arg, index)
                self.__state = CLIVisitor.State.NORMAL
            elif self.__state == CLIVisitor.State.NORMAL:
                if arg in CLIVisitor.GIT_GLOBAL_OPTS_WITH_ARG:
                    self.__global_option_with_arg = arg
                    self.__state = CLIVisitor.State.GLOBAL_OPT_WITH_ARG
                elif arg in CLIVisitor.KNOWN_OPTS:
                    self.visit_gi_option(arg, index)
                elif len(arg.split("=")) == 2 and arg.split("=")[0] in CLIVisitor.KNOWN_KWARGS:
                    self.visit_gi_kwarg(arg.split("=")[0], arg.split("=")[1], index)
                elif arg.startswith("-"):
                    self.visit_option(arg, index)
                else:
                    self.visit_parameter(arg, index)
            elif self.__state == CLIVisitor.State.GLOBAL_OPT_WITH_ARG:
                self.visit_global_option_with_arg(self.__global_option_with_arg, arg, index - 1)
                self.__global_option_with_arg = None
                self.__state = CLIVisitor.State.NORMAL

        self.__state = CLIVisitor.State.DONE


class OptParseVisitor(CLIVisitor):
    def __init__(self, argv):
        super().__init__(argv)
        self.me = None
        self.process_dashes = True
        self.bash_completion_helper = False
        self.bash_completion_cword = None
        self.bash_completion_cword_empty = False
        self.git = "git"

    def visit_me(self, me, index):
        self.me = me

    def visit_gi_option(self, option, index):
        if option == CLIVisitor.DO_NOT_PROCESS_DASHES:
            self.process_dashes = False

    def visit_gi_kwarg(self, key, value, index):
        if key == CLIVisitor.BASH_COMPLETION_HELPER:
            try:
                self.bash_completion_helper = True
                bash_completion_cword_str, bash_completion_empty_str = value.split(",")
                self.bash_completion_cword = int(bash_completion_cword_str)
                self.bash_completion_cword_empty = bash_completion_empty_str == "True"
            except ValueError:
                raise ValueError("Bad value for keyword arg {}".format(self.BASH_COMPLETION_HELPER))
        elif key == CLIVisitor.GIT:
            self.git = value


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
        visitor = OptParseVisitor(argv)
        visitor.run()

        if visitor.me is None:
            raise ValueError("argv should contain at least an executable name")

        self.me = visitor.me
        self.process_dashes = visitor.process_dashes
        self.bash_completion_helper = visitor.bash_completion_helper
        self.bash_completion_cword = visitor.bash_completion_cword
        self.bash_completion_cword_empty = visitor.bash_completion_cword_empty
        self.git = visitor.git


class CommandFindVisitor(CLIVisitor):
    class State(Enum):
        WAIT_FOR_COMMAND = 0
        WAIT_FOR_SUBCOMMAND = 1
        NORMAL = 2

    def __init__(self, argv, git="git", process_dashes=True):
        super().__init__(argv)
        self.__process_dashes = process_dashes
        self.__trie = CommandFinder(get_git_commands(git) + get_git_aliases(git), self.__process_dashes)
        self.__state = CommandFindVisitor.State.WAIT_FOR_COMMAND
        self._new_argv = []
        self.__git = git
        self.possible_commands = []
        self.command = None

    def visit_me(self, me, index):
        self._new_argv.append(self.__git)

    def visit_global_option_with_arg(self, option, arg, index):
        self._new_argv.append(option)
        self._new_argv.append(arg)

    def visit_option(self, option, index):
        self._new_argv.append(option)

    def visit_parameter(self, parameter, index):
        if self.__state == CommandFindVisitor.State.WAIT_FOR_COMMAND:
            possible_commands = self.__trie.possible_commands(parameter)
            self.possible_commands = possible_commands
            self.command = parameter
            if len(possible_commands) == 1:
                self._new_argv.append(possible_commands[0])
                if possible_commands[0] == "help":
                    # self.__trie = self.__trie
                    self.__state = CommandFindVisitor.State.WAIT_FOR_SUBCOMMAND
                else:
                    subcommands = get_git_subcommands(possible_commands[0])
                    if len(subcommands) > 0:
                        self.__state = CommandFindVisitor.State.WAIT_FOR_SUBCOMMAND
                        self.__trie = CommandFinder(subcommands, self.__process_dashes)
                    else:
                        self.__state = CommandFindVisitor.State.NORMAL
                        self.__trie = None
            else:
                self._new_argv.append(parameter)
                self.__state = CommandFindVisitor.State.NORMAL
                self.__trie = None
        elif self.__state == CommandFindVisitor.State.WAIT_FOR_SUBCOMMAND:
            possible_commands = self.__trie.possible_commands(parameter)
            self.command = "{} {}".format(self.command, parameter)
            self.possible_commands = ["{} {}".format(self.possible_commands[0], c) for c in possible_commands]

            if len(possible_commands) == 1:
                self._new_argv.append(possible_commands[0])
            else:
                self._new_argv.append(parameter)
            self.__state = CommandFindVisitor.State.NORMAL
            self.__trie = None
        else:
            self._new_argv.append(parameter)

    def visit_gi_option(self, option, index):
        pass

    def visit_gi_kwarg(self, key, value, index):
        pass

    def is_ambiguous(self):
        return len(self.possible_commands) > 1

    def is_command_unknown(self):
        return len(self.possible_commands) == 0

    def git_cli(self):
        return " ".join(shlex.quote(arg) for arg in self._new_argv)


class BashCompletionHelperVisitor(CommandFindVisitor):
    def __init__(self, argv, cword, cword_empty, git="git", process_dashes=True):
        super().__init__(argv, git, process_dashes)
        self.__cword = cword
        self.__cword_empty = cword_empty
        self.__cword_deleted = False

    def __update_cword(self, index):
        if index == self.__cword:
            self.__cword_deleted = True
        elif index < self.__cword:
            self.__cword -= 1

    def visit_gi_option(self, option, index):
        self.__update_cword(index)

    def visit_gi_kwarg(self, key, value, index):
        self.__update_cword(index)

    def bash_completion_output(self):
        def gen():
            yield self.__cword_deleted and not self.__cword_empty
            yield self.__cword
            for i, arg in enumerate(self._new_argv):
                if self.__cword == i and self.__cword_empty:
                    yield ""
                yield arg

            if self.__cword == len(self._new_argv) and self.__cword_empty:
                yield ""

        return list(gen())
