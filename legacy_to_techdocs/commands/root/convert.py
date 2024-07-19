import argparse
from typing import Any

from legacy_to_techdocs.commands.base import Command
from legacy_to_techdocs.translation import URLTranslator


class ConvertCommand(Command):
    parser_args = {
        "name": "convert",
        "help": "Convert the given API docs URL to a TechDocs URL.",
    }

    @staticmethod
    def init_arguments(command_parser: Any):
        command_parser.add_argument(
            "url", type=str, nargs="+", help="The docs URL(s) to translate."
        )

    def execute(self, args: argparse.Namespace):
        translator = URLTranslator.load_pickled()

        print(" ".join([translator.replace_urls(v)[0] for v in args.url]))
