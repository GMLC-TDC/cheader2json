import json
import pathlib
from typing import Optional

import click

from cheader2json.change_search import diffAst
from cheader2json.cheader_reader import CHeaderParser


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option()
def cli(ctx):
    """Utility to convert C header files into JSON files for use by other tools."""
    pass


@cli.command()
@click.option(
    "-f",
    "--prefix",
    help="File name prefix to use for output json files. Inferred from the name of first header file provided if not specified.",
)
@click.option(
    "--ignore-macro",
    "-i",
    envvar="IGNORED_MACROS",
    multiple=True,
    help="Macro to ignore. Can be given multiple times (if using an envvar the names are split on spaces).",
)
# Potentially useful to also support reading from stdin by passing `-` as filename?
@click.argument(
    "header",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, path_type=pathlib.Path),
)
def convert(
    header: tuple[pathlib.Path], prefix: Optional[str], ignore_macro: tuple[str]
):
    """Convert the given C headers to json files with ast and type information."""
    if not header:
        # No header files provided to convert, exit
        return
    if not prefix:
        # No prefix for output files given, derive from stem of the first header file given
        prefix = header[0].stem
    parser = CHeaderParser([str(h) for h in header], list(ignore_macro))
    with open(f"{prefix}.ast.json", "w+") as f:
        json.dump(parser.parsedInfo, f, indent=4, sort_keys=False)

    with open(f"{prefix}.types.json", "w+") as f:
        json.dump(parser._types, f, indent=4, sort_keys=False)


@cli.command()
@click.argument("oldast", type=click.File("rb"))
@click.argument("newast", type=click.File("rb"))
def diff(oldast, newast):
    """Compare two AST JSON files and print a human-readable set of changes that occurred in the header files."""
    diffAst(json.load(oldast), json.load(newast))


if __name__ == "__main__":
    cli()
