import argparse
import os
import pathlib
import re
import sys

import yaml

from typing import Dict, Tuple, List
from openapi3 import OpenAPI
from openapi3.paths import Operation

LINK_REGEX = re.compile(
    '(?:https://www.)?linode.com/docs/api/?(?P<tag>[\w-]+)?/?#?(?P<summary>[a-zA-Z0-9-]+)?(?:__[\w\-]+)?(?=[\"\s)]|$)',
    flags=re.MULTILINE,
)

URL_PATH_REGEX = re.compile(r"[^a-z ]")


def _flatten_path_for_url(value: str) -> str:
    """
    Flatten the given value into a Linode API docs URL.
    """
    return URL_PATH_REGEX.sub("", value.lower()).replace(" ", "-")


def _build_op_map(
    legacy_spec: OpenAPI,
) -> Dict[Tuple[str, str], Operation]:
    """
    Build a mapping between an API docs URL's components and its corresponding operation.
    """

    result = {}

    for path in legacy_spec.paths.values():
        for operation in [
            getattr(path, key)
            for key in ("get", "delete", "post", "put")
            if hasattr(path, key)
        ]:
            if (
                operation is None
                or operation.tags is None
                or len(operation.tags) < 1
                or operation.summary is None
            ):
                continue

            result[
                (
                    _flatten_path_for_url(operation.tags[0]),
                    _flatten_path_for_url(operation.summary),
                )
            ] = operation

    return result


def _get_equivalent_operation(
    legacy_operation: Operation, new_spec: OpenAPI
) -> Operation:
    """
    Gets the corresponding operation from the new spec for an operation in the
    legacy spec.
    """

    op_path, op_key = legacy_operation.path[-2], legacy_operation.path[-1]

    translated_path = f"/{{apiVersion}}{op_path}"

    return new_spec.resolve_path(["paths", translated_path, op_key])


def _get_target_files(path: str, recursive=False) -> List[str]:
    """
    Returns a list of files for the given path and recursive policy.
    """

    is_dir = os.path.isdir(path)
    if not is_dir:
        return [path]

    if not recursive:
        raise ValueError(
            f"Path {path} is a directory. Consider using -r to enable recursion."
        )

    result = []

    for root, _, files in os.walk(path):
        result.extend([str(pathlib.Path(root, file)) for file in files])

    return result


def _get_equivalent_link(
    new_spec: OpenAPI,
    op_map: Dict[Tuple[str, str], Operation],
    tag: str,
    summary: str,
) -> str:
    """
    Gets a TechDocs link given a legacy API docs URL's components.
    """

    op_key = (tag, summary)

    if tag is None:
        # If no tag was found, the URL was pointing at the API docs root
        return new_spec.externalDocs.url
    elif summary is None:
        # If no summary was found, link to the first operation with a matching tag
        legacy_op = next(op for key, op in op_map.items() if key[0] == tag)
    else:
        legacy_op = op_map.get(op_key)
        if legacy_op is None:
            raise ValueError(f"pair {op_key} not found in legacy spec")

    try:
        new_op = _get_equivalent_operation(legacy_op, new_spec)
    except ValueError as err:
        raise ValueError(
            f"could not get equivalent operation for {op_key}: {err}"
        )

    if new_op.externalDocs is None or new_op.externalDocs.url is None:
        raise ValueError(f"no external docs defined for {new_op}")

    return new_op.externalDocs.url


def _load_specs(args) -> Tuple[OpenAPI, OpenAPI]:
    """
    Loads and returns the legacy and new OpenAPI specs.
    """

    with open(args.legacy_spec) as f:
        legacy_spec_raw = f.read()

    with open(args.new_spec) as f:
        new_spec_raw = f.read()

    return OpenAPI(yaml.safe_load(legacy_spec_raw)), OpenAPI(
        yaml.safe_load(new_spec_raw)
    )


def command_convert(
    args,
):
    content = args.link
    if not content:
        content = sys.stdin.read()

    legacy_spec, new_spec = _load_specs(args)

    op_map = _build_op_map(legacy_spec)

    result = LINK_REGEX.sub(
        lambda match: _get_equivalent_link(
            new_spec, op_map, match["tag"], match["summary"]
        ),
        content,
    )

    sys.stdout.write(result)


def command_replace(
    args,
):
    files = []

    for path in args.path:
        files.extend(_get_target_files(path, args.recursive))

    if not args.write_result and len(files) > 1:
        raise ValueError("Cannot specify multiple files without -w.")

    legacy_spec, new_spec = _load_specs(args)

    op_map = _build_op_map(legacy_spec)

    for file in files:
        with open(file, "r") as f:
            content = f.read()

        try:
            updated_content = LINK_REGEX.sub(
                lambda match: _get_equivalent_link(
                    new_spec, op_map, match["tag"], match["summary"]
                ),
                content,
            )
        except Exception as err:
            if args.force:
                print(f"WARN: {str(err)}", file=sys.stderr)
                continue

            raise err

        if args.write_result:
            with open(file, "w") as f:
                f.write(updated_content)
        else:
            sys.stdout.write(updated_content)


def main():
    parser = argparse.ArgumentParser(
        prog="linode-docs-translator",
        description="Translate legacy linode.com/docs URLs to TechDocs URLs",
    )

    parser.add_argument(
        "-l",
        "--legacy-spec",
        help="The URL pointing to the legacy OpenAPI spec file.",
        default="openapi-legacy.yaml",
    )

    parser.add_argument(
        "-n",
        "--new-spec",
        help="The path to the new TechDocs spec file.",
        default="openapi.yaml",
    )

    subparser = parser.add_subparsers(title="subcommand", required=True)

    convert_command = subparser.add_parser(
        "convert", help="Convert the given API docs URL to a TechDocs URL."
    )
    convert_command.set_defaults(func=command_convert)

    convert_command.add_argument(
        "link", type=str, help="The docs URL to translate."
    )

    replace_command = subparser.add_parser(
        "replace",
        help="Replace all occurrences of an API docs URL in a file with their TechDocs counterparts "
        "and print the results.",
    )
    replace_command.set_defaults(func=command_replace)

    replace_command.add_argument(
        "path",
        type=str,
        nargs="+",
        help="The path to the file to replace all docs URLs in.",
    )

    replace_command.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="If specified.",
    )

    replace_command.add_argument(
        "-w",
        "--write-result",
        action="store_true",
        help="If specified, all changes will be written directly to the file.",
    )

    replace_command.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="If specified, translation errors will not prevent the operation from finishing.",
    )

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
