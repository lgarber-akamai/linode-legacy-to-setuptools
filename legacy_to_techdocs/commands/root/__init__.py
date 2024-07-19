from legacy_to_techdocs.commands.base import CommandGroup
from legacy_to_techdocs.commands.root.bake import BakeCommand
from legacy_to_techdocs.commands.root.convert import ConvertCommand
from legacy_to_techdocs.commands.root.replace import ReplaceCommand

GROUP = CommandGroup(
    "root",
    BakeCommand,
    ConvertCommand,
    ReplaceCommand,
)
