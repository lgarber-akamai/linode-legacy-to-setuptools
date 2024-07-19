import argparse
from typing import Any, Dict, Type


class Command:
    """
    Store the core functionality of a command.
    """

    parser_args: Dict[str, Any] = None

    @staticmethod
    def init_arguments(command_parser: Any):
        raise NotImplementedError

    def execute(self, args: argparse.Namespace):
        raise NotImplementedError


class CommandGroup:
    """
    Groups subcommands for simple
    """

    def __init__(
        self, name: str, *commands: Type[Command], **subparsers_args: Any
    ):
        self._name = name
        self._commands = commands
        self._subparser_args = subparsers_args or {}
        self._subparser = None

    def register(self, parser: Any) -> Any:
        """
        Registers the group under the given parser.
        """

        subparser = parser.add_subparsers(**self._subparser_args)

        for command in self._commands:
            parser = subparser.add_parser(**command.parser_args)
            command.init_arguments(parser)
            parser.set_defaults(**{self._name: command()}, required=True)

        return subparser

    def execute(self, args: argparse.Namespace):
        """
        Executes a command in the group with a
        """

        getattr(args, self._name).execute(args)
