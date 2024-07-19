import argparse
import json
import os
import pickle
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, ClassVar, Dict, List, NamedTuple, Optional, Self, Tuple, Union
from urllib.parse import urlparse

import yaml
from openapi3 import OpenAPI
from openapi3.object_base import ObjectBase
from openapi3.paths import Operation
from rich.console import Console
from rich.table import Table

from legacy_to_techdocs.shared import CONSOLE_STDERR, PICKLE_PATH
from legacy_to_techdocs.translation import URLTranslator


class Command:
    """
    Store the core functionality of a command.
    """

    @staticmethod
    def init(subparser: Any) -> argparse.ArgumentParser:
        raise NotImplementedError

    @staticmethod
    def execute(self, args: argparse.Namespace):
        raise NotImplementedError


class BakeCommand(Command):
    @staticmethod
    def init(subparser: Any) -> Any:
        command = subparser.add_parser(
            "bake",
            help="Bake the legacy and new OpenAPI specs for faster runtime execution.",
        )

        command.add_argument(
            "-l",
            "--legacy-spec",
            help="The URL pointing to the legacy OpenAPI spec file.",
            default="openapi-legacy.yaml",
        )

        command.add_argument(
            "-n",
            "--new-spec",
            help="The path to the new TechDocs spec file.",
            default="openapi.yaml",
        )

        command.add_argument(
            "-o",
            "--output-file",
            help="The file to output the baked binary to.",
            default=PICKLE_PATH,
        )

        return command

    def execute(self, args: argparse.Namespace):
        URLTranslator(
            self._load_spec(args.legacy_spec),
            self._load_spec(args.new_spec),
        ).pickle(path=args.output_file)

    @staticmethod
    def _load_spec(path: str) -> OpenAPI:
        def _parse_file() -> Dict[str, Any]:
            errors = []

            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as err:
                errors.append(str(err))

            try:
                with open(path, "r") as f:
                    return json.load(f)
            except JSONDecodeError as err:
                errors.append(str(err))

            raise ValueError(
                f"Unknown format for file {path}; got errors:\n" + "\n".join(errors)
            )

        return OpenAPI(_parse_file())


class ConvertCommand(Command):
    @staticmethod
    def init(subparser: Any) -> Any:
        command = subparser.add_parser(
            "convert", help="Convert the given API docs URL to a TechDocs URL."
        )

        command.add_argument(
            "url", type=str, nargs="+", help="The docs URL(s) to translate."
        )

        return command

    def execute(self, args: argparse.Namespace):
        translator = URLTranslator.load_pickled()

        print(" ".join([translator.replace_urls(v)[0] for v in args.url]))


class ReplaceCommand(Command):
    @staticmethod
    def init(subparser: Any) -> Any:
        command = subparser.add_parser(
            "replace",
            help="Replace all occurrences of an API docs URL in a file with their TechDocs counterparts "
            "and print the results.",
        )

        command.add_argument(
            "path",
            type=str,
            nargs="+",
            help="The path to the file to replace all docs URLs in.",
        )

        command.add_argument(
            "-w",
            "--write_changes",
            action="store_true",
            help="If specified, all changes will be written directly to the file.",
        )

        command.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="If specified, non-fatal errors will not exit immediately.",
        )

        return command

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
                before = urlparse(translation.before).path
                after = urlparse(translation.after).path

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


COMMANDS = [BakeCommand, ConvertCommand, ReplaceCommand]


def main():
    parser = argparse.ArgumentParser(
        prog="linode-docs-translator",
        description="Translate legacy linode.com/docs URLs to TechDocs URLs",
    )

    subparser = parser.add_subparsers(title="subcommand", required=True)

    for command in COMMANDS:
        command.init(subparser).set_defaults(cls=command)

    args = parser.parse_args()

    args.cls().execute(args)
