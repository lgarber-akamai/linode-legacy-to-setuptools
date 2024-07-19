import argparse
import sys
from typing import Any
from urllib.parse import urlparse

from rich.table import Table

from legacy_to_techdocs.commands.base import Command
from legacy_to_techdocs.shared import CONSOLE_STDERR
from legacy_to_techdocs.translation import URLTranslator


class ReplaceCommand(Command):
    parser_args = {
        "name": "replace",
        "help": "Replace all occurrences of an API docs URL in a file with "
        "their TechDocs counterparts and print the results.",
    }

    @staticmethod
    def init_arguments(command_parser: Any):
        command_parser.add_argument(
            "path",
            type=str,
            nargs="+",
            help="The path to the file to replace all docs URLs in.",
        )

        command_parser.add_argument(
            "-w",
            "--write_changes",
            action="store_true",
            help="If specified, all changes will be written directly to the file.",
        )

        command_parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="If specified, non-fatal errors will not exit immediately.",
        )

    def execute(self, args: argparse.Namespace):
        translator = URLTranslator.load_pickled()

        if not args.write_changes and len(args.path) > 1:
            raise ValueError(
                "--write_changes must be specified when more than one path is given"
            )

        results = []

        for file in args.path:
            with open(file, "r") as f:
                content = f.read()

            updated_content, translations = translator.replace_urls(
                content, force=args.force, path=file
            )

            for translation in translations:
                # Strip scheme & host to prevent truncation in output
                before = self._format_url_for_output(translation.before)
                after = self._format_url_for_output(translation.after)

                results.append(
                    (
                        f"[bold blue]{translation.file} ({translation.location[0]}:{translation.location[1]})",
                        f"[green]{before}[/]",
                        "=>",
                        f"[green]{after}[/]",
                    )
                )

            if args.write_changes:
                with open(file, "w") as f:
                    f.write(updated_content)
            else:
                sys.stdout.write(updated_content)

        # Logic for output table
        result_table = Table(
            show_header=False,
            box=None,
        )
        result_table.add_column(justify="right")
        result_table.add_column(justify="right")
        result_table.add_column(justify="center")
        result_table.add_column(justify="left")

        for result in sorted(results, key=lambda r: r[0]):
            result_table.add_row(*result)

        CONSOLE_STDERR.print(result_table)

    @staticmethod
    def _format_url_for_output(url: str) -> str:
        """
        Formats the given URL for the replacement output table.

        :param url: The URL to format.

        :returns: The formatted URL.
        """
        parsed = urlparse(url)
        result = parsed.path

        if parsed.fragment != "":
            result += f"#{parsed.fragment}"

        return result
