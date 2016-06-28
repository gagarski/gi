import marisa_trie


class CommandsFinder:
    """
    Class that builds a trie from available git commands and aliases and allows to
    search git commands and aliases that start with prefix
    """
    def __init__(self, commands=(), aliases=(), process_dashes=True):
        """
        Constructor.

        process_dashes specifies behavior of processing commands with dashes.

        When process_dashes is False, no special processing for commands with dashes is performed
        and command search works just like in Mercurial.

        Example:
        For prefix "comm" there are two possible commands: "commit" and "commit-tree"

        This is a bit inconvenient: if you want to commit, you cannot type just "gi comm"
        since it is an ambigouos command.

        If process_dashes is True, this case is handled.
        The commands with dashes after the given prefix are not returned as possible commands if there
        are possible commands without dashes.

        Example:
        For prefix "comm" there is only one possible command: "commit"
        For prefix "commit-t" there is only one possible command: "commit-tree"

        However, if there is no possible commands without dashes after prefix, then all commands
        with dashes are returned as possible commands.

        Example:
        For prefix "upda" there are three possible commands: "update-index", "update-ref" and "update-server-info"

        :param commands: list of git commands
        :param aliases: list of git aliases
        :param process_dashes: perform special processing for dashes in commands?
        """
        self.__trie = marisa_trie.Trie(commands + aliases)
        self.__process_dashes = process_dashes

    def possible_commands(self, prefix):
        """
        Returns list of possible commands for given prefix.
        If there is an exact match for the prefix, then it is the only possible command.
        Otherwise, the list of possible commands is returned. See also the constructor doc.
        :param prefix: prefix
        :return: list of possible commands
        """
        if prefix in self.__trie:
            # Exact match
            return [prefix]
        elif self.__trie.has_keys_with_prefix(prefix):
            # By prefix
            with_prefix = [item for (item, id) in self.__trie.items(prefix)]
            if self.__process_dashes:
                without_dashes = [item for item in with_prefix if "-" not in item[len(prefix):]]
                if len(without_dashes) == 0:
                    return with_prefix
                else:
                    return without_dashes
            else:
                return with_prefix
        else:
            return []
