import sys

import os
from pprint import pprint

from gi4git.cli import GiCli, BashCompletionHelperVisitor, CommandFindVisitor
from gi4git.git import get_git_subcommands


def gi(argv):
    """
    Executes tool
    :param argv: command line arguments
    :return:
    """
    cli = GiCli(argv)

    if cli.bash_completion_helper:
        v = BashCompletionHelperVisitor(argv=argv,
                                        cword=cli.bash_completion_cword,
                                        cword_empty=cli.bash_completion_cword_empty,
                                        git=cli.git,
                                        process_dashes=cli.process_dashes)
        v.run()
        for line in v.bash_completion_output():
            print(line)
    else:
        v = CommandFindVisitor(argv=argv,
                               git=cli.git,
                               process_dashes=cli.process_dashes)
        v.run()
        if v.is_ambiguous():
            print("{}: ambiguous git command '{}'".format(cli.me, v.command), file=sys.stderr)
            print("Possible git commands: ", file=sys.stderr)
            for cmd in v.possible_commands:
                print("  {}".format(cmd), file=sys.stderr)
        else:
            os.system(v.git_cli())
