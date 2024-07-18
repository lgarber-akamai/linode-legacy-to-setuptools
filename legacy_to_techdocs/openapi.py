import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Self, Tuple

from openapi3 import OpenAPI
from openapi3.paths import Operation

URL_PATH_IDS_REGEX = re.compile(r"{[^}]+}")


@dataclass(frozen=True)
class CondensedOperation:
    """
    A condensed version of openapi3.Operation that can be properly serialized.
    """

    @classmethod
    def from_operation(cls, op: Operation) -> Self:
        """
        Returns a CondensedOperation for a given openapi3.Operation.

        :param op: An arbitrary openapi3.Operation.
        :return: CondensedOperation
        """

        return cls(
            summary=op.summary,
            tag=op.tags[0] if len(op.tags or []) > 0 else None,
            path=_strip_url_ids(op.path[-2]),
            method=op.path[-1],
            external_docs_url=(
                op.externalDocs.url if op.externalDocs is not None else None
            ),
        )

    summary: Optional[str]
    tag: Optional[str]
    path: Optional[str]
    method: Optional[str]
    external_docs_url: Optional[str]


@dataclass(frozen=True)
class CondensedOpenAPI:
    """
    A condensed version of openapi3.OpenAPI that can be properly serialized.
    """

    @classmethod
    def from_spec(cls, spec: OpenAPI):
        """
        Returns a CondensedOpenAPI for a given openapi3.OpenAPI.

        :param spec: An arbitrary openapi3.OpenAPI spec.
        :return: CondensedOpenAPI
        """

        root_docs_url = spec.externalDocs.url if spec.externalDocs is not None else None

        paths = defaultdict()
        for path in spec.paths.values():
            for op in [getattr(path, v) for v in cls.valid_paths]:
                if op is None:
                    continue

                op_parsed = CondensedOperation.from_operation(op)
                paths[(op_parsed.path, op_parsed.method)] = op_parsed

        return cls(root_docs_url=root_docs_url, paths=paths)

    valid_paths: ClassVar[List[str]] = {"get", "post", "put", "delete"}

    root_docs_url: Optional[str]
    paths: Dict[Tuple[str, str], CondensedOperation]


def _strip_url_ids(url: str) -> str:
    """
    Removes all ID names from the given URL (e.g. /test/{id} -> /test/{})

    :param url: The URL to strip IDs from.

    :return: The updated URL.
    """

    return URL_PATH_IDS_REGEX.sub("{}", url)
