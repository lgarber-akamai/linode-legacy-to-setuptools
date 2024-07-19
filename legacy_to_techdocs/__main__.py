import argparse

from legacy_to_techdocs.commands.root import GROUP as ROOT_GROUP


def main():
    """
    Main entrypoint for this project's CLI.
    """
    parser = argparse.ArgumentParser(
        prog="linode-docs-translator",
        description="Translate legacy linode.com/docs URLs to TechDocs URLs",
    )

    ROOT_GROUP.register(parser)

    args = parser.parse_args()

    ROOT_GROUP.execute(args)
