import os
from typing import NamedTuple, Optional

from rich.console import Console

CONSOLE_STDERR = Console(stderr=True, highlight=False)

PICKLE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "specdata.bin"
)
PICKLE_PROTOCOL = 5


# Stores the identifying information from a legacy
# Linode API docs URL.
LegacyURLComponents = NamedTuple(
    "LegacyUrlComponents",
    [
        ("tag", Optional[str]),
        ("summary", Optional[str]),
        ("anchor", Optional[str]),
    ],
)
