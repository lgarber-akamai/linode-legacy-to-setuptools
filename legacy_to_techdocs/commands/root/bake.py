import argparse
import json
from json import JSONDecodeError
from typing import Any, Dict

import yaml
from openapi3 import OpenAPI

from legacy_to_techdocs.commands.base import Command
from legacy_to_techdocs.shared import PICKLE_PATH
from legacy_to_techdocs.translation import URLTranslator


class BakeCommand(Command):
    parser_args: Dict[str, Any] = {
        "name": "bake",
        "help": "Bake the legacy and new OpenAPI specs for faster runtime execution.",
    }

    @staticmethod
    def init_arguments(command: Any):
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
                f"Unknown format for file {path}; got errors:\n"
                + "\n".join(errors)
            )

        return OpenAPI(_parse_file())
