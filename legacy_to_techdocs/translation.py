import os
import pickle
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Self, Tuple, Union

from openapi3 import OpenAPI
from openapi3.object_base import ObjectBase

from legacy_to_techdocs.openapi import CondensedOpenAPI, CondensedOperation
from legacy_to_techdocs.shared import CONSOLE_STDERR, PICKLE_PATH, LegacyURLComponents

URL_PATH_REGEX = re.compile(r"[^a-zA-z0-9- ]")

LEGACY_URL_REGEX = re.compile(
    '(?:https://www.)?linode.com/docs/api/?(?P<tag>[\w-]+)?/?#?(?P<summary>[a-zA-Z0-9-]+)?(?:__(?P<anchor>[\w\-]+))?(?=["\s)]|$)',
    flags=re.MULTILINE,
)


@dataclass
class TranslationMeta:
    before: str
    after: Optional[str] = None

    file: Optional[str] = None
    location: Optional[Tuple[int, int]] = None

    @staticmethod
    def get_match_location(content: str, match: re.Match) -> Tuple[int, int]:
        """
        Returns a location tuple given the complete contents of a file and a regex match.

        :param content: The complete contents of the file.
        :param match: The match corresponding to this translation.

        :returns: The location of the match.
        """

        absolute_position = match.start()

        return (
            content.count(os.linesep, 0, absolute_position) + 1,
            absolute_position - content.rfind(os.linesep, 0, absolute_position),
        )


class TranslationError(Exception):
    """
    TranslationError represents an error with a translation operation.
    """

    def __init__(
        self, message: str, translation_meta: Optional[TranslationMeta] = None
    ):
        super().__init__(message)

        self.translation_meta = translation_meta

    def __str__(self) -> str:
        result = [super().__str__()]

        tr = self.translation_meta

        if tr:
            if tr.location:
                result.append(
                    f"line {tr.location[0]} position {tr.location[1]}",
                )

            if tr.file:
                result.append(f"in {tr.file}")

        return ", ".join(result)


class URLTranslator:
    """
    Contains the logic to translate between a legacy API spec URL and a
    TechDocs spec URL.
    """

    def __init__(self, legacy_spec: OpenAPI, new_spec: OpenAPI):
        self._legacy_spec = CondensedOpenAPI.from_spec(legacy_spec)
        self._new_spec = CondensedOpenAPI.from_spec(new_spec)
        self._legacy_op_map = self._build_op_map(self._legacy_spec)

    @classmethod
    def load_pickled(cls, path: str = PICKLE_PATH) -> Self:
        """
        Returns a new URLTranslator loaded from a pickle binary.

        :param path: (Optional) The path to the pickle binary.
        :return: The new URLTranslator.
        """
        with open(path, "rb") as f:
            return pickle.load(f)

    def pickle(self, path: str = PICKLE_PATH):
        """
        Pickles this URLTranslator and saves it to a pickle binary.

        :param path: (Optional) The path to the pickle binary.
        """

        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def _flatten_path_for_url(value: str) -> str:
        """
        Flatten the given value into a Linode API docs URL.

        :param: An arbitrary URL component.

        :returns: The flattened URL component.
        """
        return URL_PATH_REGEX.sub("", value.lower()).replace(" ", "-")

    @staticmethod
    def _build_op_map(
        legacy_spec: CondensedOpenAPI,
    ) -> Dict[Tuple[str, str], CondensedOperation]:
        """
        Build a mapping between an API docs URL's components and its corresponding operation.

        :param legacy_spec: The OpenAPI spec to build an operation map from.

        :returns: The built operation map.
        """

        result = {}

        for op in legacy_spec.paths.values():
            if op.tag is None or op.summary is None:
                continue

            result[
                URLTranslator._flatten_path_for_url(op.tag),
                URLTranslator._flatten_path_for_url(op.summary),
            ] = op

        return result

    def _translate_from_components(self, components: LegacyURLComponents) -> str:
        """
        Gets a TechDocs url given a legacy API docs URL's components.

        :param components: The components for a legacy URL.
        :return: The translated TechDocs URL.
        """

        op_key = (components.tag, components.summary)

        if components.tag is None:
            # If no tag was found, the URL was pointing at the API docs root
            return self._new_spec.root_docs_url
        elif components.summary is None:
            # If no summary was found, url to the first operation with a matching tag
            legacy_op = next(
                op
                for key, op in self._legacy_op_map.items()
                if key[0] == components.tag
            )
        else:
            legacy_op = self._legacy_op_map.get(op_key)
            if legacy_op is None:
                raise TranslationError(f"Pair {op_key} not found in legacy spec")

        try:
            new_op = self.get_equivalent_operation(legacy_op)
        except ValueError as err:
            raise TranslationError(
                f"Could not get equivalent operation for {op_key}command"
            ) from err

        if new_op.external_docs_url is None:
            raise TranslationError(f"No external docs defined for {new_op}command")

        return new_op.external_docs_url

    def get_equivalent_operation(
        self, legacy_operation: CondensedOperation
    ) -> Union[CondensedOperation, ObjectBase]:
        """
        Gets the corresponding operation from the new spec for an operation in the
        legacy spec.
        """

        key = f"/{{}}{legacy_operation.path}", legacy_operation.method

        if key not in self._new_spec.paths:
            raise TranslationError(f"Path {key} not found in new spec")

        return self._new_spec.paths[key]

    def replace_urls(
        self, target: str, force: bool = False, path: Optional[str] = None
    ) -> Tuple[str, List[TranslationMeta]]:
        """
        Replaces all legacy URLs in the given string with
        their TechDocs equivalents

        :param target: The string to replace all legacy URLs in.
        :param path: The path to the file used for this translation.
        :param force: If specified, errors will not cause an immediate exit.

        :return: The `target` attribute with all URLs replaced by TechDocs URLs.
        """
        replacements = []

        def _sub_handler(match: re.Match) -> str:
            result = match.string[match.start() : match.end()]
            meta = TranslationMeta(
                before=result,
                file=path,
                location=TranslationMeta.get_match_location(target, match),
            )

            try:
                result = self._translate_from_components(
                    LegacyURLComponents(**match.groupdict())
                )

                meta.after = result
                replacements.append(meta)
            except TranslationError as err:
                # Inject the line number and position into the error
                err.translation_meta = meta

                if not force:
                    raise err

                CONSOLE_STDERR.print(f"[yellow bold]WARN:[/] {str(err)}")

            return result

        return LEGACY_URL_REGEX.sub(_sub_handler, target), replacements
