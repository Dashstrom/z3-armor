"""Module for command line interface."""

import argparse
import logging
import pathlib
import sys
from typing import Optional, Sequence

from .algorithm import Z3Armor
from .info import __issues__, __summary__, __version__

LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
logger = logging.getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    """Prepare ArgumentParser."""
    parser = argparse.ArgumentParser(
        prog="z3-armor",
        description=__summary__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s, version {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="verbose mode, enable INFO and DEBUG messages.",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-p",
        "--secret",
        help="Secret to obfuscate, by default from stdin.",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="Seed used for generation.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--template",
        choices=["crackme.c", "solver.py"],
        help="Template to use for generate code.",
    )
    group.add_argument(
        "--template-path", help="Path to jinja template to use."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output for the file, by default on stdout.",
    )
    return parser


def setup_logging(verbose: Optional[bool] = None) -> None:
    """Do setup logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )


def entrypoint(argv: Optional[Sequence[str]] = None) -> None:
    """Entrypoint for command line interface."""
    try:
        # Get arguments
        parser = get_parser()
        args = parser.parse_args(argv)
        setup_logging(args.verbose)

        # Get secret from stdout if not provided
        secret = input() if args.secret is None else str(args.secret)

        # Create the armored program
        armored = Z3Armor(secret=secret.encode(), random_state=args.seed)
        armored.fit()
        if args.template is None:
            program = armored.format(args.template_path)
        else:
            program = armored.format(args.template)

        # Export to stdout or file
        if args.output is None:
            sys.stdout.write(program)
        else:
            pathlib.Path(args.output).write_text(program, "utf-8")

        # Report if exception occur
    except Exception as err:  # NoQA: BLE001
        logger.critical("Unexpected error", exc_info=err)
        logger.critical("Please, report this error to %s.", __issues__)
        sys.exit(1)
